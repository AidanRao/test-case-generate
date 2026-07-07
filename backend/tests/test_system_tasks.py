import json
import os
import tempfile
import unittest
from unittest.mock import patch

from app.storage.json_storage import JsonStorage
from app.scheduler import scheduler, register_handler, shutdown_scheduler, start_scheduler


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
        register_handler("uniportal_sync", storage.synchronize_uniportal)
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
        register_handler("uniportal_sync", storage.synchronize_uniportal)
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


if __name__ == "__main__":
    unittest.main()
