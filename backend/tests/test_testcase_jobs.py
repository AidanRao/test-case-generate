import os
import tempfile
import time
import unittest
from threading import Event
from unittest.mock import patch


class _BlockingGenerator:
    def __init__(self, result):
        self.result = result
        self.started = Event()
        self.release = Event()

    def generate_test_cases(self, *args, **kwargs):
        self.started.set()
        if not self.release.wait(timeout=5):
            raise TimeoutError("test generator was not released")
        return self.result


class TestCaseGenerationJobsTest(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmpdir.cleanup)
        self.environment = patch.dict(
            os.environ,
            {"DATA_DIR": self.tmpdir.name, "UNIPORTAL_SYNC_ENABLED": "false"},
            clear=False,
        )
        self.environment.start()
        self.addCleanup(self.environment.stop)

        from app import create_app

        self.app = create_app()
        self.app.testing = True
        self.client = self.app.test_client()
        self.manager = self.app.extensions["testcase_job_manager"]
        self.addCleanup(lambda: self.manager.shutdown(wait=True))

        response = self.client.post(
            "/v1/projects",
            json={
                "code": "PRJ-JOBS",
                "title": "任务测试项目",
                "requirements": [
                    {
                        "module": "登录",
                        "requirements": [
                            {
                                "title": "用户登录",
                                "type": "功能需求",
                                "code": "REQ-LOGIN",
                                "content": "用户可以登录",
                            },
                            {
                                "title": "用户退出",
                                "type": "功能需求",
                                "code": "REQ-LOGOUT",
                                "content": "用户可以退出",
                            },
                        ],
                    }
                ],
            },
        )
        self.project_id = response.get_json()["data"]["id"]
        self.requirements = self.app.config["STORAGE"].list_requirements(
            self.project_id
        )

    @staticmethod
    def _generated_cases(title="新生成用例"):
        return [
            {
                "title": title,
                "test_case_type": "功能测试",
                "scenario_type": "正常流程用例",
                "test_steps": [
                    {"step_desc": "执行操作", "expectation": "操作成功"}
                ],
            }
        ]

    def _wait_for_terminal_status(self, job_id, timeout=3):
        deadline = time.time() + timeout
        while time.time() < deadline:
            job = self.manager.get_job(job_id)
            if job and not job["active"]:
                return job
            time.sleep(0.01)
        self.fail(f"job {job_id} did not finish")

    def test_project_status_returns_exact_active_requirements_and_progress(self):
        generator = _BlockingGenerator(self._generated_cases())
        target_id = self.requirements[0]["id"]
        with patch(
            "app.services.testcase_service.TestCaseService._build_generator",
            return_value=generator,
        ):
            submitted = self.client.post(
                f"/v1/projects/{self.project_id}/testcase-generation-jobs",
                json={"requirement_ids": [target_id], "replace": True},
            )
            self.assertEqual(submitted.status_code, 202)
            job_id = submitted.get_json()["data"]["job_id"]
            self.assertTrue(generator.started.wait(timeout=1))

            status = self.client.get(
                f"/v1/projects/{self.project_id}/testcase-generation-jobs"
            ).get_json()["data"]
            self.assertTrue(status["active"])
            self.assertEqual(status["status"], "running")
            self.assertEqual(status["requirement_ids"], [target_id])
            self.assertEqual(status["active_requirement_ids"], [target_id])
            self.assertEqual(status["current_requirement_id"], target_id)
            self.assertEqual(status["completed_count"], 0)
            self.assertEqual(status["total_count"], 1)

            duplicate = self.client.post(
                f"/v1/projects/{self.project_id}/testcase-generation-jobs",
                json={"requirement_ids": [self.requirements[1]["id"]]},
            )
            self.assertEqual(duplicate.status_code, 409)
            self.assertEqual(duplicate.get_json()["data"]["job_id"], job_id)

            concurrent_update = self.client.put(
                f"/v1/projects/{self.project_id}/requirements/{target_id}",
                json={"title": "生成期间不允许修改"},
            )
            self.assertEqual(concurrent_update.status_code, 409)
            self.assertEqual(concurrent_update.get_json()["code"], 40902)

            generator.release.set()
            completed = self._wait_for_terminal_status(job_id)

        self.assertEqual(completed["status"], "completed")
        self.assertFalse(completed["active"])
        self.assertEqual(completed["active_requirement_ids"], [])
        self.assertEqual(completed["completed_requirement_ids"], [target_id])

    def test_failed_replacement_keeps_existing_testcases(self):
        target = self.requirements[0]
        storage = self.app.config["STORAGE"]
        storage.add_testcases(
            self.project_id,
            target["id"],
            [
                {
                    "id": "existing-case",
                    "requirement_code": target["code"],
                    "requirement_id": target["id"],
                    "title": "原有用例",
                    "code": "TC-PRJ-JOBS-001",
                    "type": "功能测试",
                    "scenario_type": "正常流程用例",
                    "test_steps": [],
                }
            ],
        )
        generator = _BlockingGenerator(None)
        with patch(
            "app.services.testcase_service.TestCaseService._build_generator",
            return_value=generator,
        ):
            submitted = self.client.post(
                f"/v1/projects/{self.project_id}/testcase-generation-jobs",
                json={"requirement_ids": [target["id"]], "replace": True},
            )
            job_id = submitted.get_json()["data"]["job_id"]
            self.assertTrue(generator.started.wait(timeout=1))
            before_failure = storage.list_testcases(self.project_id, target["id"])
            self.assertEqual([item["id"] for item in before_failure], ["existing-case"])

            generator.release.set()
            failed = self._wait_for_terminal_status(job_id)

        self.assertEqual(failed["status"], "failed")
        self.assertEqual(failed["error"], "generation_failed")
        after_failure = storage.list_testcases(self.project_id, target["id"])
        self.assertEqual([item["id"] for item in after_failure], ["existing-case"])

    def test_successful_replacement_is_committed_after_generation(self):
        target = self.requirements[0]
        storage = self.app.config["STORAGE"]
        storage.add_testcases(
            self.project_id,
            target["id"],
            [
                {
                    "id": "existing-case",
                    "requirement_code": target["code"],
                    "requirement_id": target["id"],
                    "title": "原有用例",
                    "code": "TC-PRJ-JOBS-001",
                    "type": "功能测试",
                    "scenario_type": "正常流程用例",
                    "test_steps": [],
                }
            ],
        )
        generator = _BlockingGenerator(self._generated_cases("替换后的用例"))
        with patch(
            "app.services.testcase_service.TestCaseService._build_generator",
            return_value=generator,
        ):
            submitted = self.client.post(
                f"/v1/projects/{self.project_id}/testcase-generation-jobs",
                json={"requirement_ids": [target["id"]], "replace": True},
            )
            job_id = submitted.get_json()["data"]["job_id"]
            self.assertTrue(generator.started.wait(timeout=1))
            self.assertEqual(
                storage.list_testcases(self.project_id, target["id"])[0]["title"],
                "原有用例",
            )

            generator.release.set()
            completed = self._wait_for_terminal_status(job_id)

        self.assertEqual(completed["status"], "completed")
        stored = storage.list_testcases(self.project_id, target["id"])
        self.assertEqual(len(stored), 1)
        self.assertEqual(stored[0]["title"], "替换后的用例")

    def test_rejects_invalid_requirement_ids_before_creating_job(self):
        response = self.client.post(
            f"/v1/projects/{self.project_id}/testcase-generation-jobs",
            json={"requirement_ids": ["missing-requirement"]},
        )

        self.assertEqual(response.status_code, 404)
        status = self.manager.get_project_status(self.project_id)
        self.assertEqual(status["status"], "idle")


if __name__ == "__main__":
    unittest.main()
