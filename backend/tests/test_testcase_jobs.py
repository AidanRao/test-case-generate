import os
import tempfile
import time
import unittest
from threading import Event, Lock
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


class _ConcurrentBlockingGenerator:
    def __init__(self, result, expected_starts):
        self.result = result
        self.expected_starts = expected_starts
        self.all_started = Event()
        self.release = Event()
        self.lock = Lock()
        self.active_count = 0
        self.max_active_count = 0
        self.started_ids = []

    def generate_test_cases(
        self,
        requirement_content,
        item_id,
        item_title,
        **kwargs,
    ):
        with self.lock:
            self.active_count += 1
            self.max_active_count = max(self.max_active_count, self.active_count)
            self.started_ids.append(str(item_id))
            if len(self.started_ids) == self.expected_starts:
                self.all_started.set()
        try:
            if not self.release.wait(timeout=5):
                raise TimeoutError("test generator was not released")
            return self.result
        finally:
            with self.lock:
                self.active_count -= 1


class _ResultByRequirementGenerator:
    def __init__(self, results):
        self.results = results

    def generate_test_cases(
        self,
        requirement_content,
        item_id,
        item_title,
        **kwargs,
    ):
        result = self.results[str(item_id)]
        if isinstance(result, Exception):
            raise result
        return result


class _FastAndSlowGenerator:
    def __init__(self, slow_id, fast_id, result):
        self.slow_id = str(slow_id)
        self.fast_id = str(fast_id)
        self.result = result
        self.slow_started = Event()
        self.fast_finished = Event()
        self.release_slow = Event()

    def generate_test_cases(
        self,
        requirement_content,
        item_id,
        item_title,
        **kwargs,
    ):
        requirement_id = str(item_id)
        if requirement_id == self.slow_id:
            self.slow_started.set()
            if not self.release_slow.wait(timeout=5):
                raise TimeoutError("slow generator was not released")
            return self.result
        if requirement_id == self.fast_id:
            if not self.slow_started.wait(timeout=1):
                raise TimeoutError("slow generator did not start")
            self.fast_finished.set()
            return self.result
        raise AssertionError(f"unexpected requirement id: {requirement_id}")


class TestCaseGenerationJobsTest(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmpdir.cleanup)
        self.environment = patch.dict(
            os.environ,
            {
                "DATA_DIR": self.tmpdir.name,
                "UNIPORTAL_SYNC_ENABLED": "false",
                "TESTCASE_REQUIREMENT_WORKERS": "1",
            },
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

    def test_requirement_worker_count_comes_from_environment(self):
        from app.config import AppConfig

        self.assertEqual(
            self.app.config["APP_CONFIG"].testcase_requirement_workers,
            1,
        )
        with patch.dict(os.environ, {}, clear=True):
            self.assertEqual(AppConfig().testcase_requirement_workers, 2)
        with patch.dict(
            os.environ,
            {"TESTCASE_REQUIREMENT_WORKERS": "3"},
            clear=False,
        ):
            self.assertEqual(AppConfig().testcase_requirement_workers, 3)

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
            self.assertEqual(status["processing_requirement_ids"], [target_id])
            self.assertNotIn("current_requirement_id", status)
            self.assertEqual(status["completed_count"], 0)
            self.assertEqual(status["failed_count"], 0)
            self.assertEqual(status["processed_count"], 0)
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
        self.assertEqual(completed["processing_requirement_ids"], [])
        self.assertEqual(completed["completed_requirement_ids"], [target_id])
        self.assertEqual(completed["failed_requirement_ids"], [])
        self.assertEqual(completed["processed_count"], 1)

    def test_requirement_worker_limit_runs_requests_concurrently(self):
        self.app.config["APP_CONFIG"].testcase_requirement_workers = 2
        generator = _ConcurrentBlockingGenerator(
            self._generated_cases(),
            expected_starts=2,
        )
        requirement_ids = [item["id"] for item in self.requirements]
        with patch(
            "app.services.testcase_service.TestCaseService._build_generator",
            return_value=generator,
        ):
            submitted = self.client.post(
                f"/v1/projects/{self.project_id}/testcase-generation-jobs",
                json={"requirement_ids": requirement_ids, "replace": True},
            )
            job_id = submitted.get_json()["data"]["job_id"]
            self.assertTrue(generator.all_started.wait(timeout=1))

            running = self.manager.get_job(job_id)
            self.assertEqual(
                running["processing_requirement_ids"],
                requirement_ids,
            )
            self.assertEqual(generator.max_active_count, 2)

            generator.release.set()
            completed = self._wait_for_terminal_status(job_id)

        self.assertEqual(completed["status"], "completed")
        self.assertCountEqual(
            completed["completed_requirement_ids"],
            requirement_ids,
        )
        self.assertEqual(completed["failed_requirement_ids"], [])
        stored = self.app.config["STORAGE"].list_project_testcases(self.project_id)
        self.assertCountEqual(
            [item["requirement_id"] for item in stored],
            requirement_ids,
        )
        self.assertEqual(
            [item["code"] for item in stored],
            ["TC-PRJ-JOBS-001", "TC-PRJ-JOBS-002"],
        )

    def test_processing_requirements_only_include_active_worker_slots(self):
        self.app.config["APP_CONFIG"].testcase_requirement_workers = 1
        generator = _ConcurrentBlockingGenerator(
            self._generated_cases(),
            expected_starts=1,
        )
        requirement_ids = [item["id"] for item in self.requirements]
        with patch(
            "app.services.testcase_service.TestCaseService._build_generator",
            return_value=generator,
        ):
            submitted = self.client.post(
                f"/v1/projects/{self.project_id}/testcase-generation-jobs",
                json={"requirement_ids": requirement_ids, "replace": True},
            )
            job_id = submitted.get_json()["data"]["job_id"]
            self.assertTrue(generator.all_started.wait(timeout=1))

            running = self.manager.get_job(job_id)
            self.assertEqual(
                running["processing_requirement_ids"],
                [requirement_ids[0]],
            )
            self.assertEqual(
                running["active_requirement_ids"],
                requirement_ids,
            )

            generator.release.set()
            completed = self._wait_for_terminal_status(job_id)

        self.assertEqual(completed["status"], "completed")
        self.assertEqual(completed["processing_requirement_ids"], [])

    def test_completed_requirement_is_persisted_before_other_requests_finish(self):
        self.app.config["APP_CONFIG"].testcase_requirement_workers = 2
        slow_id = self.requirements[0]["id"]
        fast_id = self.requirements[1]["id"]
        generator = _FastAndSlowGenerator(
            slow_id,
            fast_id,
            self._generated_cases(),
        )
        storage = self.app.config["STORAGE"]
        with patch(
            "app.services.testcase_service.TestCaseService._build_generator",
            return_value=generator,
        ):
            submitted = self.client.post(
                f"/v1/projects/{self.project_id}/testcase-generation-jobs",
                json={"requirement_ids": [slow_id, fast_id], "replace": True},
            )
            job_id = submitted.get_json()["data"]["job_id"]
            self.assertTrue(generator.fast_finished.wait(timeout=1))

            deadline = time.time() + 1
            fast_cases = []
            while time.time() < deadline:
                fast_cases = storage.list_testcases(self.project_id, fast_id)
                if fast_cases:
                    break
                time.sleep(0.01)

            self.assertEqual(len(fast_cases), 1)
            self.assertEqual(fast_cases[0]["code"], "TC-PRJ-JOBS-001")
            self.assertEqual(storage.list_testcases(self.project_id, slow_id), [])
            running = self.manager.get_job(job_id)
            self.assertTrue(running["active"])
            self.assertEqual(running["processing_requirement_ids"], [slow_id])
            self.assertEqual(running["completed_requirement_ids"], [fast_id])

            generator.release_slow.set()
            completed = self._wait_for_terminal_status(job_id)

        self.assertEqual(
            completed["completed_requirement_ids"],
            [fast_id, slow_id],
        )
        self.assertEqual(
            [
                item["code"]
                for item in storage.list_project_testcases(self.project_id)
            ],
            ["TC-PRJ-JOBS-001", "TC-PRJ-JOBS-002"],
        )

    def test_partial_failure_continues_and_records_failed_requirement(self):
        self.app.config["APP_CONFIG"].testcase_requirement_workers = 2
        failed_id = self.requirements[0]["id"]
        completed_id = self.requirements[1]["id"]
        generator = _ResultByRequirementGenerator(
            {
                failed_id: None,
                completed_id: self._generated_cases("成功需求用例"),
            }
        )
        with patch(
            "app.services.testcase_service.TestCaseService._build_generator",
            return_value=generator,
        ):
            submitted = self.client.post(
                f"/v1/projects/{self.project_id}/testcase-generation-jobs",
                json={
                    "requirement_ids": [failed_id, completed_id],
                    "replace": True,
                },
            )
            failed = self._wait_for_terminal_status(
                submitted.get_json()["data"]["job_id"]
            )

        self.assertEqual(failed["status"], "failed")
        self.assertEqual(failed["error"], "generation_failed")
        self.assertEqual(failed["completed_requirement_ids"], [completed_id])
        self.assertEqual(failed["failed_requirement_ids"], [failed_id])
        self.assertEqual(failed["completed_count"], 1)
        self.assertEqual(failed["failed_count"], 1)
        self.assertEqual(failed["processed_count"], 2)
        storage = self.app.config["STORAGE"]
        self.assertEqual(storage.list_testcases(self.project_id, failed_id), [])
        self.assertEqual(
            storage.list_testcases(self.project_id, completed_id)[0]["title"],
            "成功需求用例",
        )
        quality = storage.get_project_quality(self.project_id)
        self.assertEqual(quality["success_count"], 1)
        self.assertEqual(quality["fail_count"], 1)

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
        self.assertEqual(failed["failed_requirement_ids"], [target["id"]])
        self.assertEqual(failed["failed_count"], 1)
        self.assertEqual(failed["processed_count"], 1)
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
