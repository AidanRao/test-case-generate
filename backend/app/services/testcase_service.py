import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass

from openai import OpenAI

from app.utils.ids import new_uuid
from app.models.testcase import DEFAULT_PRIORITY, is_valid_scenario_type
from testcase_generator import TestCaseGenerator


class TestCaseGenerationError(RuntimeError):
    def __init__(self, code):
        super().__init__(code)
        self.code = code


@dataclass
class RequirementGenerationResult:
    index: int
    requirement: dict
    raw_cases: list | None = None
    error: str | None = None


class TestCaseService:
    def __init__(self, storage, config):
        self.storage = storage
        self.config = config

    def generate_testcases(
        self,
        project_id,
        requirements,
        replace=False,
        ai_config=None,
        on_requirement_started=None,
        on_requirement_finished=None,
        on_requirement_completed=None,
        on_requirement_failed=None,
    ):
        started_at = time.time()
        requirements = list(requirements)
        results = []
        completed_count = 0
        failures = []

        try:
            generator = self._build_generator(ai_config)
            if generator is None:
                raise TestCaseGenerationError("missing_api_key")
            generation_results = self.iter_requirement_cases(
                requirements,
                generator=generator,
                on_requirement_started=on_requirement_started,
                on_requirement_finished=on_requirement_finished,
            )
        except TestCaseGenerationError as exc:
            for requirement in requirements:
                requirement_id = str(requirement["id"])
                failures.append((requirement_id, exc.code))
                if on_requirement_failed:
                    on_requirement_failed(requirement_id)
            self._save_generation_quality(
                project_id,
                started_at,
                len(requirements),
                completed_count,
                fail_count=len(failures),
            )
            raise

        for generation_result in generation_results:
            requirement = generation_result.requirement
            requirement_id = str(requirement["id"])
            failure_code = generation_result.error
            try:
                if failure_code:
                    raise TestCaseGenerationError(failure_code)
                if not self.storage.get_requirement(project_id, requirement_id):
                    raise TestCaseGenerationError("requirement_not_found")
                mapped = self._map_cases(
                    project_id,
                    requirement,
                    generation_result.raw_cases,
                )
                if replace:
                    self.storage.replace_testcases_by_requirement(
                        project_id, requirement.get("id"), mapped
                    )
                else:
                    self.storage.add_testcases(project_id, requirement.get("id"), mapped)
                results.extend(mapped)
                completed_count += 1
                if on_requirement_completed:
                    on_requirement_completed(requirement_id)
            except TestCaseGenerationError as exc:
                failures.append((requirement_id, exc.code))
                if on_requirement_failed:
                    on_requirement_failed(requirement_id)
            except Exception as exc:
                failures.append(
                    (requirement_id, f"internal_error:{exc.__class__.__name__}")
                )
                if on_requirement_failed:
                    on_requirement_failed(requirement_id)

        self._save_generation_quality(
            project_id,
            started_at,
            len(requirements),
            completed_count,
            fail_count=len(failures),
        )
        if failures:
            raise TestCaseGenerationError(failures[0][1])
        return results

    def generate_requirement_cases(
        self,
        requirements,
        ai_config=None,
        generator=None,
        include_module_info=False,
        on_requirement_started=None,
        on_requirement_finished=None,
    ):
        results = list(
            self.iter_requirement_cases(
                requirements,
                ai_config=ai_config,
                generator=generator,
                include_module_info=include_module_info,
                on_requirement_started=on_requirement_started,
                on_requirement_finished=on_requirement_finished,
            )
        )
        return sorted(results, key=lambda result: result.index)

    def iter_requirement_cases(
        self,
        requirements,
        ai_config=None,
        generator=None,
        include_module_info=False,
        on_requirement_started=None,
        on_requirement_finished=None,
    ):
        requirements = list(requirements)
        if not requirements:
            return
        generator = generator or self._build_generator(ai_config)
        if generator is None:
            raise TestCaseGenerationError("missing_api_key")

        worker_count = min(
            self.config.testcase_requirement_workers,
            len(requirements),
        )
        with ThreadPoolExecutor(
            max_workers=worker_count,
            thread_name_prefix="testcase-requirement",
        ) as executor:
            futures = {
                executor.submit(
                    self._generate_requirement_cases,
                    index,
                    generator,
                    requirement,
                    include_module_info,
                    on_requirement_started,
                    on_requirement_finished,
                ): index
                for index, requirement in enumerate(requirements)
            }
            for future in as_completed(futures):
                yield future.result()

    def _generate_requirement_cases(
        self,
        index,
        generator,
        requirement,
        include_module_info,
        on_requirement_started,
        on_requirement_finished,
    ):
        requirement_id = str(requirement["id"])
        if on_requirement_started:
            on_requirement_started(requirement_id)
        try:
            kwargs = {"req_type": self._map_req_type(requirement.get("type"))}
            if include_module_info:
                kwargs["module_info"] = requirement.get("module")
            raw_cases = generator.generate_test_cases(
                requirement.get("content", ""),
                requirement.get("id"),
                requirement.get("title", ""),
                **kwargs,
            )
            if raw_cases is None or not self.has_valid_scenarios(raw_cases):
                return RequirementGenerationResult(
                    index=index,
                    requirement=requirement,
                    error="generation_failed",
                )
            return RequirementGenerationResult(
                index=index,
                requirement=requirement,
                raw_cases=raw_cases,
            )
        except Exception as exc:
            return RequirementGenerationResult(
                index=index,
                requirement=requirement,
                error=f"internal_error:{exc.__class__.__name__}",
            )
        finally:
            if on_requirement_finished:
                on_requirement_finished(requirement_id)

    def list_testcases(self, project_id, requirement_id):
        return self.storage.list_testcases(project_id, requirement_id)

    def update_testcase(self, project_id, testcase_id, payload):
        return self.storage.update_testcase(project_id, testcase_id, payload)

    def delete_testcase(self, project_id, testcase_id):
        return self.storage.delete_testcase(project_id, testcase_id)

    def _build_generator(self, ai_config=None):
        effective_config = self._get_effective_ai_config(ai_config)
        if not effective_config.get("api_key"):
            return None
        client = OpenAI(
            api_key=effective_config["api_key"],
            base_url=effective_config.get("base_url") or None
        )
        return TestCaseGenerator(client, effective_config.get("model"))

    def _get_effective_ai_config(self, ai_config=None):
        if ai_config and ai_config.get("api_key"):
            return {
                "api_key": ai_config["api_key"],
                "base_url": ai_config.get("base_url", ""),
                "model": ai_config.get("model", "") or self.config.ai_model,
            }
        user_config = self.storage.get_ai_config()
        if user_config and user_config.get("api_key"):
            return {
                "api_key": user_config["api_key"],
                "base_url": user_config.get("base_url", ""),
                "model": user_config.get("model", "") or self.config.ai_model,
            }
        return {
            "api_key": self.config.ai_api_key,
            "base_url": self.config.ai_base_url,
            "model": self.config.ai_model,
        }

    def _map_req_type(self, requirement_type):
        return str(requirement_type or "功能需求").replace("需求", "测试")

    def _save_generation_quality(
        self, project_id, started_at, attempted_count, completed_count, fail_count
    ):
        self.storage.save_project_quality(
            project_id,
            {
                "duration": time.time() - started_at,
                "fail_count": fail_count,
                "iterations": attempted_count,
                "success_count": completed_count,
            },
        )

    def has_valid_scenarios(self, raw_cases):
        return bool(raw_cases) and all(
            isinstance(case, dict)
            and is_valid_scenario_type(case.get("scenario_type"))
            for case in raw_cases
        )

    def _map_cases(self, project_id, requirement, raw_cases):
        existing = self.storage.list_project_testcases(project_id)
        project = self.storage.get_project(project_id) or {}
        project_code = project.get("code") or str(project_id)
        items = []
        base_seq = len(existing) + 1
        for idx, case in enumerate(raw_cases):
            seq = str(base_seq + idx).zfill(3)
            case_title = case.get("title")
            if not case_title:
                case_title = f"{requirement.get('title', '')}-用例{seq}"
            item = {
                "requirement_code": requirement.get("code", ""),
                "requirement_id": requirement.get("id"),
                "id": new_uuid(),
                "title": case_title,
                "code": f"TC-{project_code}-{seq}",
                "type": case.get("test_case_type") or "功能测试",
                "scenario_type": case["scenario_type"],
                "priority": DEFAULT_PRIORITY,
                "test_steps": case.get("test_steps", []),
                "test_target_desc": case.get("test_target_desc", ""),
                "verify_method": case.get("verify_method", "TESTING"),
            }
            items.append(item)
        return items
