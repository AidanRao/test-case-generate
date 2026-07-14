import json
import os
import tempfile
import unittest
from unittest.mock import patch

from app.storage.json_storage import JsonStorage
from app.scheduler import SystemTaskManager


class SystemTasksTest(unittest.TestCase):
    def setUp(self):
        self.local = tempfile.TemporaryDirectory()
        self.shared = tempfile.TemporaryDirectory()
        self.addCleanup(self.local.cleanup)
        self.addCleanup(self.shared.cleanup)

    def create_manager(self, storage, enabled=True, interval_seconds=30):
        with patch.dict(
            os.environ,
            {
                "UNIPORTAL_SYNC_ENABLED": "true" if enabled else "false",
                "UNIPORTAL_SYNC_INTERVAL_SECONDS": str(interval_seconds),
            },
            clear=False,
        ):
            manager = SystemTaskManager(storage.system_task_store, storage)
            manager.start()
        self.addCleanup(manager.shutdown)
        return manager

    def test_task_config_is_persisted_and_can_start_sync_runner(self):
        storage = JsonStorage(self.local.name, self.shared.name)
        manager = self.create_manager(storage, enabled=False, interval_seconds=30)

        initial = manager.list_tasks()[0]
        self.assertEqual(initial["id"], "uniportal_sync")
        self.assertFalse(initial["enabled"])
        self.assertEqual(initial["interval_seconds"], 30)
        self.assertEqual(
            initial["kwargs"],
            {"requirement_path": "document-validator/requirement.json"},
        )
        self.assertFalse(initial["running"])

        updated = manager.update_task(
            "uniportal_sync",
            {
                "enabled": True,
                "interval_seconds": 15,
                "kwargs": {"requirement_path": "custom/requirement.json"},
            },
        )
        self.assertTrue(updated["enabled"])
        self.assertEqual(updated["interval_seconds"], 15)
        self.assertEqual(
            updated["kwargs"], {"requirement_path": "custom/requirement.json"}
        )
        self.assertTrue(updated["running"])

        with open(
            os.path.join(self.local.name, "system_tasks.json"),
            "r",
            encoding="utf-8",
        ) as source:
            stored = json.load(source)[0]
        self.assertTrue(stored["enabled"])
        self.assertEqual(stored["interval_seconds"], 15)
        self.assertEqual(
            stored["kwargs"], {"requirement_path": "custom/requirement.json"}
        )
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
            self.addCleanup(app.extensions["system_task_manager"].shutdown)
            app.testing = True
            client = app.test_client()

            initial = client.get("/v1/system/tasks").get_json()["data"]["list"][0]
            self.assertFalse(initial["enabled"])
            self.assertEqual(initial["interval_seconds"], 30)
            self.assertEqual(
                initial["kwargs"],
                {"requirement_path": "document-validator/requirement.json"},
            )
            self.assertTrue(initial["available"])

            invalid = client.put(
                "/v1/system/tasks/uniportal_sync",
                json={"enabled": True, "interval_seconds": 2},
            )
            self.assertEqual(invalid.status_code, 400)

            response = client.put(
                "/v1/system/tasks/uniportal_sync",
                json={
                    "enabled": True,
                    "interval_seconds": 20,
                    "kwargs": {"requirement_path": "custom/requirement.json"},
                },
            )
            self.assertEqual(response.status_code, 200)
            task = response.get_json()["data"]
            self.assertTrue(task["enabled"])
            self.assertEqual(task["interval_seconds"], 20)
            self.assertEqual(
                task["kwargs"], {"requirement_path": "custom/requirement.json"}
            )
            self.assertTrue(task["running"])

            disabled = client.put(
                "/v1/system/tasks/uniportal_sync",
                json={"enabled": False, "interval_seconds": 20},
            ).get_json()["data"]
            self.assertFalse(disabled["enabled"])
            self.assertFalse(disabled["running"])

    def test_running_task_stays_scheduled_after_manual_run(self):
        storage = JsonStorage(self.local.name, self.shared.name)
        manager = self.create_manager(storage, enabled=True, interval_seconds=30)
        manager.update_task(
            "uniportal_sync",
            {
                "enabled": True,
                "interval_seconds": 15,
                "kwargs": {"requirement_path": "custom/requirement.json"},
            },
        )

        with patch.object(storage, "synchronize_uniportal") as synchronize:
            task = manager.run_task("uniportal_sync")

        synchronize.assert_called_once_with("custom/requirement.json")
        self.assertTrue(task["running"])
        self.assertEqual(
            manager.scheduler.get_job("uniportal_sync").kwargs["requirement_path"],
            "custom/requirement.json",
        )

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
            self.addCleanup(app.extensions["system_task_manager"].shutdown)
            app.testing = True
            storage = app.config["STORAGE"]
            client = app.test_client()

            with patch.object(storage, "synchronize_uniportal") as synchronize:
                response = client.post("/v1/system/tasks/uniportal_sync/run")

            self.assertEqual(response.status_code, 200)
            self.assertFalse(response.get_json()["data"]["enabled"])
            synchronize.assert_called_once_with("document-validator/requirement.json")

            missing = client.post("/v1/system/tasks/missing/run")
            self.assertEqual(missing.status_code, 404)

    def test_manual_uniportal_run_uses_registered_kwargs(self):
        storage = JsonStorage(self.local.name, self.shared.name)
        manager = self.create_manager(storage, enabled=True, interval_seconds=30)

        with patch.object(storage, "synchronize_uniportal") as synchronize:
            manager.run_task("uniportal_sync")

        synchronize.assert_called_once_with("document-validator/requirement.json")

        manager.update_task(
            "uniportal_sync",
            {
                "enabled": True,
                "interval_seconds": 30,
                "kwargs": {"requirement_path": "custom/requirement.json"},
            },
        )

        with patch.object(storage, "synchronize_uniportal") as synchronize:
            manager.run_task("uniportal_sync")

        synchronize.assert_called_once_with("custom/requirement.json")

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
        with open(
            os.path.join(self.local.name, "system_tasks.json"),
            "w",
            encoding="utf-8",
        ) as target:
            json.dump(
                [
                    {
                        "id": "uniportal_sync",
                        "type": "uniportal_sync",
                        "name": "UniPortal 项目同步",
                        "description": "定期从 UniPortal 同步项目和需求数据",
                        "enabled": True,
                        "interval_seconds": 42,
                        "kwargs": {"requirement_path": "custom/requirement.json"},
                    }
                ],
                target,
            )
        storage = JsonStorage(self.local.name, self.shared.name)
        manager = self.create_manager(storage, enabled=False, interval_seconds=30)

        stored = storage.system_task_store.get_task("uniportal_sync")
        self.assertTrue(stored["enabled"])
        self.assertEqual(stored["interval_seconds"], 42)
        self.assertEqual(
            stored["kwargs"], {"requirement_path": "custom/requirement.json"}
        )
        job = manager.scheduler.get_job("uniportal_sync")
        self.assertIsNotNone(job)
        self.assertEqual(job.trigger.interval.total_seconds(), 42)
        self.assertEqual(job.kwargs["requirement_path"], "custom/requirement.json")


if __name__ == "__main__":
    unittest.main()
