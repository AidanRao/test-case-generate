import json
import os
import tempfile
import threading
import time
import unittest
from unittest.mock import patch


class _Message:
    def __init__(self, content):
        self.content = content


class _Choice:
    def __init__(self, content):
        self.message = _Message(content)


class _Response:
    def __init__(self, content):
        self.choices = [_Choice(content)]


class _Completions:
    def __init__(self, responder):
        self.responder = responder
        self.requests = []
        self.lock = threading.Lock()

    def create(self, **kwargs):
        with self.lock:
            self.requests.append(kwargs)
        result = self.responder(kwargs) if callable(self.responder) else self.responder
        return _Response("```json\n" + json.dumps(result, ensure_ascii=False) + "\n```")


class _Chat:
    def __init__(self, responder):
        self.completions = _Completions(responder)


class _Client:
    def __init__(self, responder):
        self.chat = _Chat(responder)


class CoverageAnalysisTest(unittest.TestCase):
    def setUp(self):
        self.data_dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.data_dir.cleanup)
        self.env_patch = patch.dict(
            os.environ,
            {"DATA_DIR": self.data_dir.name},
            clear=False,
        )
        self.env_patch.start()
        self.addCleanup(self.env_patch.stop)

        from app import create_app

        self.app = create_app()
        self.app.testing = True
        self.client = self.app.test_client()
        self.coverage_manager = self.app.extensions["coverage_job_manager"]
        self.addCleanup(lambda: self.coverage_manager.shutdown(wait=True))

    def _create_project(self, requirement_count=2, with_testcases=True):
        requirement_payloads = [
            {
                "code": f"REQ-{index + 1}",
                "title": f"需求 {index + 1}",
                "type": "功能需求",
                "content": f"功能 {index + 1}，包含 api_{index + 1} 接口和 value 参数。",
            }
            for index in range(requirement_count)
        ]
        response = self.client.post(
            "/v1/projects",
            json={
                "code": f"COVERAGE-{requirement_count}",
                "title": "覆盖率项目",
                "requirements": [
                    {
                        "module": "认证",
                        "requirements": requirement_payloads,
                    }
                ],
            },
        )
        project_id = response.get_json()["data"]["id"]
        requirements = self.app.config["STORAGE"].list_requirements(project_id)
        if with_testcases:
            for index, requirement in enumerate(requirements):
                self.app.config["STORAGE"].add_testcases(
                    project_id,
                    requirement["id"],
                    [
                        {
                            "id": f"TC-{index + 1}",
                            "title": f"需求 {index + 1} 正常用例",
                            "code": f"TC-COVERAGE-{index + 1:03d}",
                            "type": "功能测试",
                            "scenario_type": "正常流程用例",
                            "test_steps": [
                                {
                                    "step_desc": f"输入合法 value {index + 1}",
                                    "expectation": "处理成功",
                                }
                            ],
                        }
                    ],
                )
        return project_id, requirements

    @staticmethod
    def _request_payload(kwargs):
        content = kwargs["messages"][1]["content"]
        return json.loads(content.split("\n", 1)[1])

    @classmethod
    def _successful_result(cls, kwargs, include_interfaces=True):
        payload = cls._request_payload(kwargs)
        testcase_id = payload["requirement"]["testcases"][0]["id"]
        result = {
            "feature_points": [
                {
                    "name": payload["requirement"]["title"] + " 功能点",
                    "covered": True,
                    "evidence_testcase_ids": [testcase_id],
                }
            ],
            "interfaces": [],
        }
        if include_interfaces:
            result["interfaces"] = [
                {
                    "interface_name": "primary_api",
                    "parameters": [
                        {
                            "name": "value",
                            "covered": True,
                            "tested_conditions": ["合法值"],
                            "evidence_testcase_ids": [testcase_id],
                        }
                    ],
                },
                {
                    "interface_name": "secondary_api",
                    "parameters": [
                        {
                            "name": "limit",
                            "covered": False,
                            "tested_conditions": [],
                            "evidence_testcase_ids": [],
                        }
                    ],
                },
            ]
        return result

    def _wait_for_terminal_status(self, job_id, timeout=5):
        deadline = time.time() + timeout
        while time.time() < deadline:
            job = self.coverage_manager.get_job(job_id)
            if job and not job["active"]:
                return job
            time.sleep(0.01)
        self.fail(f"coverage job {job_id} did not finish")

    def _calculate_and_wait(self, project_id):
        response = self.client.post(
            f"/v1/projects/{project_id}/coverage/calculate"
        )
        self.assertEqual(response.status_code, 202)
        job_id = response.get_json()["data"]["job_id"]
        terminal = self._wait_for_terminal_status(job_id)
        coverage = self.client.get(
            f"/v1/projects/{project_id}/coverage"
        ).get_json()["data"]
        return terminal, coverage

    def test_analyzes_each_requirement_and_aggregates_project_coverage(self):
        project_id, requirements = self._create_project()
        fake_client = _Client(self._successful_result)

        with patch(
            "app.services.coverage_service.CoverageService._build_client",
            return_value=(fake_client, "coverage-model"),
        ):
            job, result = self._calculate_and_wait(project_id)

        self.assertEqual(job["status"], "completed")
        self.assertEqual(job["completed_count"], 2)
        self.assertEqual(job["total_count"], 2)
        self.assertEqual(
            result["feature_point_coverage"],
            {"total": 2, "covered": 2, "rate": 1.0},
        )
        self.assertEqual(
            result["interface_coverage"],
            {"total": 4, "covered": 2, "rate": 0.5},
        )
        self.assertEqual(len(result["feature_point_details"]), 2)
        self.assertEqual(len(result["interface_details"][0]["interfaces"]), 2)
        self.assertEqual(result["schema_version"], 3)
        self.assertEqual(
            result["feature_point_details"][0]["points"][0]["evidence_testcases"],
            [
                {
                    "id": "TC-1",
                    "code": "TC-COVERAGE-001",
                    "title": "需求 1 正常用例",
                }
            ],
        )
        self.assertEqual(
            result["interface_details"][0]["interfaces"][0]["parameters"][0][
                "evidence_testcases"
            ][0]["title"],
            "需求 1 正常用例",
        )
        self.assertEqual(len(fake_client.chat.completions.requests), 2)

        request_requirement_ids = set()
        for request in fake_client.chat.completions.requests:
            payload = self._request_payload(request)
            self.assertIn("requirement", payload)
            self.assertNotIn("requirements", payload)
            request_requirement_ids.add(payload["requirement"]["id"])
            self.assertEqual(len(payload["requirement"]["testcases"]), 1)
        self.assertEqual(
            request_requirement_ids,
            {str(item["id"]) for item in requirements},
        )

        queried = self.client.get(
            f"/v1/projects/{project_id}/coverage"
        ).get_json()["data"]
        self.assertEqual(queried, result)

    def test_evidence_is_limited_to_current_requirement_testcases(self):
        project_id, requirements = self._create_project()

        def cross_requirement_evidence(kwargs):
            result = self._successful_result(kwargs, include_interfaces=False)
            payload = self._request_payload(kwargs)
            if payload["requirement"]["id"] == requirements[1]["id"]:
                result["feature_points"][0]["evidence_testcase_ids"] = ["TC-1"]
            return result

        fake_client = _Client(cross_requirement_evidence)
        with patch(
            "app.services.coverage_service.CoverageService._build_client",
            return_value=(fake_client, "coverage-model"),
        ):
            job, result = self._calculate_and_wait(project_id)

        self.assertEqual(job["status"], "completed")
        self.assertEqual(
            result["feature_point_coverage"],
            {"total": 2, "covered": 1, "rate": 0.5},
        )
        second_point = result["feature_point_details"][1]["points"][0]
        self.assertFalse(second_point["covered"])
        self.assertEqual(second_point["evidence_testcases"], [])

    def test_failure_preserves_previous_saved_result(self):
        project_id, requirements = self._create_project()
        previous = {
            "schema_version": 3,
            "feature_point_coverage": {"total": 1, "covered": 0, "rate": 0},
            "interface_coverage": {"total": 0, "covered": 0, "rate": 0},
            "feature_point_details": [],
            "interface_details": [],
            "calculated_at": "2026-01-01T00:00:00+00:00",
            "duration": 1,
            "model": "old-model",
        }
        self.app.config["STORAGE"].save_project_coverage(project_id, previous)

        def fail_one_requirement(kwargs):
            payload = self._request_payload(kwargs)
            if payload["requirement"]["id"] == requirements[1]["id"]:
                raise RuntimeError("provider failed")
            return self._successful_result(kwargs)

        fake_client = _Client(fail_one_requirement)
        with patch(
            "app.services.coverage_service.CoverageService._build_client",
            return_value=(fake_client, "coverage-model"),
        ):
            job, _ = self._calculate_and_wait(project_id)

        self.assertEqual(job["status"], "failed")
        self.assertEqual(job["error"], "internal_error:RuntimeError")
        queried = self.client.get(
            f"/v1/projects/{project_id}/coverage"
        ).get_json()["data"]
        self.assertEqual(queried["calculated_at"], previous["calculated_at"])
        self.assertEqual(queried["model"], "old-model")

    def test_no_testcases_and_no_interfaces_produce_zero_coverage(self):
        project_id, _ = self._create_project(
            requirement_count=1,
            with_testcases=False,
        )
        fake_client = _Client(
            {
                "feature_points": [
                    {
                        "name": "未验证功能",
                        "covered": True,
                        "evidence_testcase_ids": ["invented-case"],
                    }
                ],
                "interfaces": [],
            }
        )

        with patch(
            "app.services.coverage_service.CoverageService._build_client",
            return_value=(fake_client, "coverage-model"),
        ):
            job, result = self._calculate_and_wait(project_id)

        self.assertEqual(job["status"], "completed")
        self.assertEqual(
            result["feature_point_coverage"],
            {"total": 1, "covered": 0, "rate": 0.0},
        )
        self.assertEqual(
            result["interface_coverage"],
            {"total": 0, "covered": 0, "rate": 0},
        )
        self.assertEqual(result["interface_details"][0]["interfaces"], [])

    def test_uses_at_most_four_workers_and_preserves_requirement_order(self):
        from app.services.coverage_service import CoverageService

        project_id, requirements = self._create_project(
            requirement_count=6,
            with_testcases=False,
        )
        service = CoverageService(
            self.app.config["STORAGE"],
            self.app.config["APP_CONFIG"],
        )
        active = 0
        maximum_active = 0
        lock = threading.Lock()

        def analyze(_client, _model, _project, requirement, _testcases):
            nonlocal active, maximum_active
            with lock:
                active += 1
                maximum_active = max(maximum_active, active)
            time.sleep(0.03)
            with lock:
                active -= 1
            return {"requirement_id": requirement["id"]}

        with patch.object(service, "_analyze_requirement", side_effect=analyze):
            results = service._analyze_requirements(
                object(),
                "model",
                self.app.config["STORAGE"].get_project(project_id),
                requirements,
                {},
            )

        self.assertGreater(maximum_active, 1)
        self.assertLessEqual(maximum_active, 4)
        self.assertEqual(
            [item["requirement_id"] for item in results],
            [item["id"] for item in requirements],
        )

    def test_query_returns_null_before_first_calculation(self):
        project_id, _ = self._create_project(requirement_count=1)

        response = self.client.get(f"/v1/projects/{project_id}/coverage")

        self.assertEqual(response.status_code, 200)
        self.assertIsNone(response.get_json()["data"])

    def test_query_ignores_incompatible_saved_schema(self):
        project_id, _ = self._create_project(requirement_count=1)
        self.app.config["STORAGE"].save_project_coverage(
            project_id,
            {
                "schema_version": 2,
                "feature_point_coverage": {"total": 1, "covered": 1, "rate": 1},
            },
        )

        response = self.client.get(f"/v1/projects/{project_id}/coverage")

        self.assertEqual(response.status_code, 200)
        self.assertIsNone(response.get_json()["data"])

    def test_calculation_requires_requirements(self):
        project_id = self.client.post(
            "/v1/projects",
            json={"code": "EMPTY-COVERAGE", "title": "空项目"},
        ).get_json()["data"]["id"]

        response = self.client.post(
            f"/v1/projects/{project_id}/coverage/calculate"
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.get_json()["code"], 40001)

    def test_async_status_and_duplicate_submission(self):
        from app.services.coverage_service import CoverageService

        project_id, requirements = self._create_project(requirement_count=1)
        started = threading.Event()
        release = threading.Event()

        def blocking_calculation(_service, _project_id, on_requirement_completed=None):
            started.set()
            if not release.wait(timeout=3):
                raise TimeoutError("coverage calculation was not released")
            if on_requirement_completed:
                on_requirement_completed(requirements[0]["id"])

        with patch.object(
            CoverageService,
            "calculate_coverage",
            new=blocking_calculation,
        ):
            submitted = self.client.post(
                f"/v1/projects/{project_id}/coverage/calculate"
            )
            self.assertEqual(submitted.status_code, 202)
            job_id = submitted.get_json()["data"]["job_id"]
            self.assertTrue(started.wait(timeout=1))

            project_status = self.client.get(
                f"/v1/projects/{project_id}/coverage/calculation-jobs"
            )
            self.assertEqual(project_status.status_code, 200)
            running = project_status.get_json()["data"]
            self.assertEqual(running["job_id"], job_id)
            self.assertEqual(running["status"], "running")
            self.assertTrue(running["active"])
            self.assertEqual(running["completed_count"], 0)
            self.assertEqual(running["total_count"], 1)

            job_status = self.client.get(
                f"/v1/projects/{project_id}/coverage/calculation-jobs/{job_id}"
            )
            self.assertEqual(job_status.status_code, 200)
            self.assertEqual(job_status.get_json()["data"]["job_id"], job_id)

            duplicate = self.client.post(
                f"/v1/projects/{project_id}/coverage/calculate"
            )
            self.assertEqual(duplicate.status_code, 409)
            self.assertEqual(duplicate.get_json()["code"], 40903)
            self.assertEqual(duplicate.get_json()["data"]["job_id"], job_id)

            release.set()
            completed = self._wait_for_terminal_status(job_id)

        self.assertEqual(completed["status"], "completed")
        self.assertEqual(completed["completed_count"], 1)


if __name__ == "__main__":
    unittest.main()
