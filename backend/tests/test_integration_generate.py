import json
import os
import tempfile
import unittest
from threading import Event, Lock
from unittest.mock import patch


class _StubGenerator:
    def __init__(self, cases_by_req_id):
        self.cases_by_req_id = cases_by_req_id

    def generate_test_cases(self, requirement_content, item_id, item_title, req_type="功能测试", **kwargs):
        return self.cases_by_req_id.get(str(item_id))


class _OutOfOrderGenerator(_StubGenerator):
    def __init__(self, cases_by_req_id, first_id, second_id):
        super().__init__(cases_by_req_id)
        self.first_id = first_id
        self.second_id = second_id
        self.second_finished = Event()
        self.lock = Lock()
        self.active_count = 0
        self.max_active_count = 0

    def generate_test_cases(
        self,
        requirement_content,
        item_id,
        item_title,
        req_type="功能测试",
        **kwargs,
    ):
        with self.lock:
            self.active_count += 1
            self.max_active_count = max(self.max_active_count, self.active_count)
        try:
            if str(item_id) == self.first_id:
                if not self.second_finished.wait(timeout=2):
                    raise TimeoutError("second requirement did not finish")
            elif str(item_id) == self.second_id:
                self.second_finished.set()
            return super().generate_test_cases(
                requirement_content,
                item_id,
                item_title,
                req_type=req_type,
                **kwargs,
            )
        finally:
            with self.lock:
                self.active_count -= 1


class IntegrationGenerateTestcasesTest(unittest.TestCase):
    def _create_app_and_client(self, requirement_workers=1):
        tmpdir = tempfile.TemporaryDirectory()
        self.addCleanup(tmpdir.cleanup)
        from app import create_app

        with patch.dict(
            os.environ,
            {
                "DATA_DIR": tmpdir.name,
                "TESTCASE_REQUIREMENT_WORKERS": str(requirement_workers),
                "UNIPORTAL_SYNC_ENABLED": "false",
            },
            clear=False,
        ):
            app = create_app()
        app.testing = True
        self.addCleanup(
            lambda: app.extensions["testcase_job_manager"].shutdown(wait=True)
        )
        self.addCleanup(
            lambda: app.extensions["coverage_job_manager"].shutdown(wait=True)
        )
        return app, app.test_client()

    def test_format_excel_not_supported(self):
        app, client = self._create_app_and_client()
        payload = {
            "requirements": [
                {
                    "module": "M1",
                    "requirements": [
                        {
                            "title": "R1",
                            "type": "功能需求",
                            "code": "REQ-1",
                            "content": "x",
                        }
                    ],
                }
            ],
            "format": "excel",
        }
        resp = client.post("/v1/integration/testcases/generate", json=payload)
        self.assertEqual(resp.status_code, 400)

    def test_returns_json_format_with_iterations_formula(self):
        app, client = self._create_app_and_client()
        req_id_1 = "req-1"
        req_id_2 = "req-2"
        stub = _StubGenerator(
            {
                req_id_1: [
                    {
                        "title": "C1",
                        "test_case_type": "功能测试",
                        "scenario_type": "正常流程用例",
                        "test_steps": [{"step_desc": "s1", "expectation": "e1"}],
                        "test_target_desc": "t1",
                        "verify_method": "TESTING",
                    }
                ],
                req_id_2: [
                    {
                        "title": "C2",
                        "test_case_type": "安全性测试",
                        "scenario_type": "异常场景用例",
                        "test_steps": [{"step_desc": "s2", "expectation": "e2"}],
                        "test_target_desc": "t2",
                        "verify_method": "TESTING",
                    }
                ],
            }
        )
        payload = {
            "requirements": [
                {
                    "module": "M1",
                    "requirements": [
                        {"id": req_id_1, "title": "R1", "type": "功能需求", "code": "REQ-1", "content": "x"},
                        {"id": req_id_2, "title": "R2", "type": "安全需求", "code": "REQ-2", "content": "y"},
                    ],
                }
            ],
            "format": "json",
        }
        with (
            patch("app.services.testcase_service.TestCaseService._build_generator", return_value=stub),
            patch("random.uniform", return_value=1.5),
            patch("random.randint", return_value=2),
        ):
            resp = client.post("/v1/integration/testcases/generate", json=payload)
        self.assertEqual(resp.status_code, 200)
        data = resp.get_json()
        self.assertIn("quality_info", data)
        self.assertIn("test_case", data)
        self.assertIsInstance(data["test_case"], list)
        self.assertEqual(data["test_case"][0]["scenario_type"], "正常流程用例")
        self.assertEqual(data["test_case"][1]["scenario_type"], "异常场景用例")
        self.assertEqual(data["test_case"][0]["priority"], "P1")
        self.assertEqual(data["test_case"][1]["priority"], "P1")
        self.assertEqual(data["quality_info"]["success_count"], 2)
        self.assertEqual(data["quality_info"]["fail_count"], 0)
        self.assertEqual(data["quality_info"]["iterations"], 5)
        self.assertNotIn("req_type_stats", data["quality_info"])

    def test_concurrent_generation_preserves_input_order_without_saving(self):
        app, client = self._create_app_and_client(requirement_workers=2)
        req_id_1 = "req-slow"
        req_id_2 = "req-fast"
        stub = _OutOfOrderGenerator(
            {
                req_id_1: [
                    {
                        "title": "C1",
                        "scenario_type": "正常流程用例",
                        "test_steps": [],
                    }
                ],
                req_id_2: [
                    {
                        "title": "C2",
                        "scenario_type": "异常场景用例",
                        "test_steps": [],
                    }
                ],
            },
            first_id=req_id_1,
            second_id=req_id_2,
        )
        payload = {
            "requirements": [
                {
                    "module": "M1",
                    "requirements": [
                        {
                            "id": req_id_1,
                            "title": "R1",
                            "type": "功能需求",
                            "code": "REQ-1",
                            "content": "x",
                        },
                        {
                            "id": req_id_2,
                            "title": "R2",
                            "type": "功能需求",
                            "code": "REQ-2",
                            "content": "y",
                        },
                    ],
                }
            ],
            "format": "json",
            "is_save": False,
        }
        with patch(
            "app.services.testcase_service.TestCaseService._build_generator",
            return_value=stub,
        ):
            response = client.post(
                "/v1/integration/testcases/generate",
                json=payload,
            )

        self.assertEqual(response.status_code, 200)
        testcases = response.get_json()["test_case"]
        self.assertEqual(stub.max_active_count, 2)
        self.assertEqual([item["title"] for item in testcases], ["C1", "C2"])
        self.assertEqual(
            [item["code"] for item in testcases],
            ["TC-INTEGRATION-001", "TC-INTEGRATION-002"],
        )

    def test_saved_generation_continues_after_requirement_failure(self):
        app, client = self._create_app_and_client(requirement_workers=2)
        stub = _StubGenerator(
            {
                "req-failed": None,
                "req-success": [
                    {
                        "title": "C2",
                        "scenario_type": "正常流程用例",
                        "test_steps": [],
                    }
                ],
            }
        )
        payload = {
            "requirements": [
                {
                    "module": "M1",
                    "requirements": [
                        {
                            "id": "req-failed",
                            "title": "R1",
                            "type": "功能需求",
                            "code": "REQ-1",
                            "content": "x",
                        },
                        {
                            "id": "req-success",
                            "title": "R2",
                            "type": "功能需求",
                            "code": "REQ-2",
                            "content": "y",
                        },
                    ],
                }
            ],
            "format": "json",
        }
        with patch(
            "app.services.testcase_service.TestCaseService._build_generator",
            return_value=stub,
        ):
            response = client.post(
                "/v1/integration/testcases/generate",
                json=payload,
            )

        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertEqual(data["quality_info"]["fail_count"], 1)
        self.assertEqual([item["title"] for item in data["test_case"]], ["C2"])
        project_id = app.config["STORAGE"].list_projects()[0]["id"]
        self.assertEqual(
            app.config["STORAGE"].list_project_testcases(project_id)[0]["title"],
            "C2",
        )

    def test_saved_generation_quality_can_be_loaded_by_project(self):
        app, client = self._create_app_and_client()
        req_id = "req-quality"
        stub = _StubGenerator(
            {
                req_id: [
                    {
                        "title": "C1",
                        "test_case_type": "性能测试",
                        "scenario_type": "边界条件用例",
                        "test_steps": [{"step_desc": "s1", "expectation": "e1"}],
                        "test_target_desc": "t1",
                        "verify_method": "TESTING",
                    }
                ],
            }
        )
        payload = {
            "requirements": [
                {
                    "module": "M1",
                    "requirements": [
                        {"id": req_id, "title": "R1", "type": "性能需求", "code": "REQ-1", "content": "x"},
                    ],
                }
            ],
            "format": "json",
        }
        with (
            patch("app.services.testcase_service.TestCaseService._build_generator", return_value=stub),
            patch("app.routes.testcases._calculate_iterations", return_value=7),
        ):
            resp = client.post("/v1/integration/testcases/generate", json=payload)

        self.assertEqual(resp.status_code, 200)
        projects = app.config["STORAGE"].list_projects()
        self.assertEqual(len(projects), 1)

        quality_resp = client.get(f"/v1/projects/{projects[0]['id']}/quality")
        self.assertEqual(quality_resp.status_code, 200)
        quality = quality_resp.get_json()["data"]
        self.assertEqual(quality["iterations"], 7)
        self.assertIsInstance(quality["duration"], (int, float))
        self.assertEqual(quality["success_count"], 1)
        self.assertNotIn("req_type_stats", quality)

        stored_quality = app.config["STORAGE"].get_project_quality(projects[0]["id"])
        self.assertNotIn("req_type_stats", stored_quality)

        quality_path = os.path.join(app.config["STORAGE"].data_dir, "quality.json")
        with open(quality_path, "r", encoding="utf-8") as source:
            quality_records = json.load(source)
        self.assertIsInstance(quality_records, list)
        self.assertEqual(len(quality_records), 1)
        self.assertEqual(quality_records[0]["project_id"], projects[0]["id"])
        self.assertEqual(quality_records[0]["iterations"], 7)
        self.assertNotIn("req_type_stats", quality_records[0])


if __name__ == "__main__":
    unittest.main()
