from openai import OpenAI

from app.utils.ids import new_uuid
from testcase_generator import TestCaseGenerator


class TestCaseService:
    def __init__(self, storage, config):
        self.storage = storage
        self.config = config

    def generate_testcases(self, project_id, requirement_ids, replace=False):
        generator = self._build_generator()
        if generator is None:
            return None, "missing_api_key"
        results = []
        for requirement_id in requirement_ids:
            requirement = self.storage.get_requirement(project_id, requirement_id)
            if not requirement:
                return None, "requirement_not_found"
            req_type = self._map_req_type(requirement.get("type"))
            raw_cases = generator.generate_test_cases(
                requirement.get("content", ""),
                requirement.get("id"),
                requirement.get("title", ""),
                req_type=req_type,
            )
            if raw_cases is None:
                return None, "generation_failed"
            mapped = self._map_cases(project_id, requirement, raw_cases)
            if replace:
                self.storage.delete_testcases_by_requirement(
                    project_id, requirement.get("id")
                )
            self.storage.add_testcases(project_id, requirement.get("id"), mapped)
            results.extend(mapped)
        return results, None

    def list_testcases(self, project_id, requirement_id):
        return self.storage.list_testcases(project_id, requirement_id)

    def update_testcase(self, project_id, testcase_id, payload):
        return self.storage.update_testcase(project_id, testcase_id, payload)

    def delete_testcase(self, project_id, testcase_id):
        return self.storage.delete_testcase(project_id, testcase_id)

    def _build_generator(self):
        if not self.config.ai_api_key:
            return None
        client = OpenAI(api_key=self.config.ai_api_key, base_url=self.config.ai_base_url or None)
        return TestCaseGenerator(client, self.config.ai_model)

    def _map_req_type(self, requirement_type):
        return requirement_type.replace("需求", "测试")

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
                "test_steps": case.get("test_steps", []),
                "test_target_desc": case.get("test_target_desc", ""),
                "verify_method": case.get("verify_method", "TESTING"),
            }
            items.append(item)
        return items
