import os
import tempfile
import unittest
from unittest.mock import patch


class _StubGenerator:
    def __init__(self, cases_by_req_id):
        self.cases_by_req_id = cases_by_req_id

    def generate_test_cases(self, requirement_content, item_id, item_title, req_type="功能测试", **kwargs):
        return self.cases_by_req_id.get(str(item_id))


class IntegrationGenerateTestcasesTest(unittest.TestCase):
    def _create_app_and_client(self):
        tmpdir = tempfile.TemporaryDirectory()
        self.addCleanup(tmpdir.cleanup)
        os.environ["DATA_DIR"] = tmpdir.name
        from app import create_app

        app = create_app()
        app.testing = True
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
                        "test_steps": [{"step_desc": "s1", "expectation": "e1"}],
                        "test_target_desc": "t1",
                        "verify_method": "TESTING",
                    }
                ],
                req_id_2: [
                    {
                        "title": "C2",
                        "test_case_type": "安全性测试",
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
        self.assertEqual(data["quality_info"]["success_count"], 2)
        self.assertEqual(data["quality_info"]["fail_count"], 0)
        self.assertEqual(data["quality_info"]["iterations"], 5)
        self.assertEqual(data["quality_info"]["req_type_stats"]["功能测试"], 1)
        self.assertEqual(data["quality_info"]["req_type_stats"]["安全性测试"], 1)


if __name__ == "__main__":
    unittest.main()

