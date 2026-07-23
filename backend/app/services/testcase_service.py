import time

from openai import OpenAI

from app.utils.ids import new_uuid
from app.models.testcase import DEFAULT_PRIORITY, is_valid_scenario_type
from testcase_generator import TestCaseGenerator


class TestCaseGenerationError(RuntimeError):
    def __init__(self, code):
        super().__init__(code)
        self.code = code


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
        on_requirement_completed=None,
    ):
        started_at = time.time()
        generator = self._build_generator(ai_config)
        if generator is None:
            raise TestCaseGenerationError("missing_api_key")
        results = []
        completed_count = 0
        attempted_count = 0
        try:
            for requirement in requirements:
                requirement_id = str(requirement["id"])
                attempted_count += 1
                if on_requirement_started:
                    on_requirement_started(requirement_id)
                req_type = self._map_req_type(requirement.get("type"))
                raw_cases = generator.generate_test_cases(
                    requirement.get("content", ""),
                    requirement.get("id"),
                    requirement.get("title", ""),
                    req_type=req_type,
                )
                if raw_cases is None or not self.has_valid_scenarios(raw_cases):
                    raise TestCaseGenerationError("generation_failed")
                mapped = self._map_cases(project_id, requirement, raw_cases)
                if not self.storage.get_requirement(project_id, requirement_id):
                    raise TestCaseGenerationError("requirement_not_found")
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
        except Exception:
            self._save_generation_quality(
                project_id,
                started_at,
                attempted_count,
                completed_count,
                fail_count=1,
            )
            raise

        self._save_generation_quality(
            project_id,
            started_at,
            attempted_count,
            completed_count,
            fail_count=0,
        )
        return results

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
