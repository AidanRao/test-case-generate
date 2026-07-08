import json
import os
import tempfile
import unittest
from unittest.mock import patch

from app.storage.json_storage import JsonStorage
from app.scheduler import scheduler, shutdown_scheduler, start_scheduler


class SystemTasksTest(unittest.TestCase):
    def setUp(self):
        self.local = tempfile.TemporaryDirectory()
        self.shared = tempfile.TemporaryDirectory()
        self.addCleanup(self.local.cleanup)
        self.addCleanup(self.shared.cleanup)
        shutdown_scheduler()

    def tearDown(self):
        shutdown_scheduler()

    def test_task_config_is_persisted_and_can_start_sync_runner(self):
        storage = JsonStorage(self.local.name, self.shared.name, False, 30)
        from app.scheduler import sync_default_jobs

        sync_default_jobs(
            scheduler,
            storage.system_task_store,
            runtime_kwargs={"uniportal_sync": {"storage": storage}},
            default_overrides={
                "uniportal_sync": {"enabled": False, "interval_seconds": 30}
            },
        )
        start_scheduler()

        initial = storage.list_system_tasks(scheduler)[0]
        self.assertEqual(initial["id"], "uniportal_sync")
        self.assertFalse(initial["enabled"])
        self.assertEqual(initial["interval_seconds"], 30)
        self.assertFalse(initial["running"])

        updated = storage.save_system_task(
            "uniportal_sync", {"enabled": True, "interval_seconds": 15}, scheduler
        )
        self.assertTrue(updated["enabled"])
        self.assertEqual(updated["interval_seconds"], 15)
        self.assertTrue(updated["running"])

        with open(os.path.join(self.local.name, "system_tasks.json"), "r", encoding="utf-8") as source:
            stored = json.load(source)["tasks"][0]
        self.assertTrue(stored["enabled"])
        self.assertEqual(stored["interval_seconds"], 15)
        self.assertNotIn("trigger", stored)

    def test_system_task_api_validates_and_applies_updates(self):
        with patch.dict(
            os.environ,
            {
                "DATA_DIR": self.local.name,
                "UNIPORTAL_STORAGE_PATH": self.shared.name,
                "UNIPORTAL_SYNC_ENABLED": "false",
                "UNIPORTAL_SYNC_INTERVAL_SECONDS": "30",
            },
            clear=False,
        ):
            from app import create_app

            app = create_app()
            app.testing = True
            client = app.test_client()

            initial = client.get("/v1/system/tasks").get_json()["data"]["list"][0]
            self.assertFalse(initial["enabled"])
            self.assertEqual(initial["interval_seconds"], 30)
            self.assertTrue(initial["available"])

            invalid = client.put(
                "/v1/system/tasks/uniportal_sync",
                json={"enabled": True, "interval_seconds": 2},
            )
            self.assertEqual(invalid.status_code, 400)

            response = client.put(
                "/v1/system/tasks/uniportal_sync",
                json={"enabled": True, "interval_seconds": 20},
            )
            self.assertEqual(response.status_code, 200)
            task = response.get_json()["data"]
            self.assertTrue(task["enabled"])
            self.assertEqual(task["interval_seconds"], 20)
            self.assertTrue(task["running"])

            disabled = client.put(
                "/v1/system/tasks/uniportal_sync",
                json={"enabled": False, "interval_seconds": 20},
            ).get_json()["data"]
            self.assertFalse(disabled["enabled"])
            self.assertFalse(disabled["running"])

    def test_running_task_stays_scheduled_after_manual_run(self):
        storage = JsonStorage(self.local.name, self.shared.name, True, 30)
        from app.scheduler import sync_default_jobs

        sync_default_jobs(
            scheduler,
            storage.system_task_store,
            runtime_kwargs={"uniportal_sync": {"storage": storage}},
            default_overrides={
                "uniportal_sync": {"enabled": True, "interval_seconds": 30}
            },
        )
        storage.save_system_task(
            "uniportal_sync", {"enabled": True, "interval_seconds": 15}, scheduler
        )
        start_scheduler()

        with patch.object(storage, "synchronize_uniportal") as synchronize:
            task = storage.run_system_task("uniportal_sync", scheduler)

        synchronize.assert_called_once_with()
        self.assertTrue(task["running"])

    def test_system_task_can_be_run_once_while_schedule_is_disabled(self):
        with patch.dict(
            os.environ,
            {
                "DATA_DIR": self.local.name,
                "UNIPORTAL_STORAGE_PATH": self.shared.name,
                "UNIPORTAL_SYNC_ENABLED": "false",
            },
            clear=False,
        ):
            from app import create_app

            app = create_app()
            app.testing = True
            storage = app.config["STORAGE"]
            client = app.test_client()

            with patch.object(storage, "synchronize_uniportal") as synchronize:
                response = client.post("/v1/system/tasks/uniportal_sync/run")

            self.assertEqual(response.status_code, 200)
            self.assertFalse(response.get_json()["data"]["enabled"])
            synchronize.assert_called_once_with()

            missing = client.post("/v1/system/tasks/missing/run")
            self.assertEqual(missing.status_code, 404)

    def test_scheduled_task_decorator_registers_metadata(self):
        from app.task_registry import TASK_REGISTRY, scheduled_task

        before_count = len(TASK_REGISTRY)

        @scheduled_task(
            id="test_registry_task",
            name="测试任务",
            description="用于测试注册表",
            kwargs={"value": 1},
            seconds=10,
        )
        def sample_task(value=None):
            return value

        self.addCleanup(lambda: TASK_REGISTRY.pop())
        self.assertEqual(len(TASK_REGISTRY), before_count + 1)
        task = TASK_REGISTRY[-1]
        self.assertEqual(task.id, "test_registry_task")
        self.assertIs(task.func, sample_task)
        self.assertEqual(task.interval_seconds, 10)
        self.assertEqual(task.kwargs, {"value": 1})

    def test_registry_sync_adds_missing_task_and_preserves_existing_config(self):
        from app.scheduler import sync_default_jobs

        with open(os.path.join(self.local.name, "system_tasks.json"), "w", encoding="utf-8") as target:
            json.dump(
                {
                    "tasks": [
                        {
                            "id": "uniportal_sync",
                            "type": "uniportal_sync",
                            "name": "UniPortal 项目同步",
                            "description": "定期从 UniPortal 同步项目和需求数据",
                            "enabled": True,
                            "interval_seconds": 42,
                        }
                    ]
                },
                target,
            )
        storage = JsonStorage(self.local.name, self.shared.name, False, 30)

        sync_default_jobs(
            scheduler,
            storage.system_task_store,
            runtime_kwargs={"uniportal_sync": {"storage": storage}},
            default_overrides={
                "uniportal_sync": {"enabled": False, "interval_seconds": 30}
            },
        )
        start_scheduler()

        stored = storage.system_task_store.get_task("uniportal_sync")
        self.assertTrue(stored["enabled"])
        self.assertEqual(stored["interval_seconds"], 42)
        job = scheduler.get_job("uniportal_sync")
        self.assertIsNotNone(job)
        self.assertEqual(job.trigger.interval.total_seconds(), 42)


if __name__ == "__main__":
    unittest.main()
