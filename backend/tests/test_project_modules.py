import os
import tempfile
import unittest
from unittest.mock import patch


class ProjectModulesTest(unittest.TestCase):
    def setUp(self):
        self.local = tempfile.TemporaryDirectory()
        self.shared = tempfile.TemporaryDirectory()
        self.addCleanup(self.local.cleanup)
        self.addCleanup(self.shared.cleanup)

    def _client(self):
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
            return app.test_client()

    def test_can_create_empty_project_module(self):
        client = self._client()
        project_id = client.post(
            "/v1/projects",
            json={"code": "PRJ-MOD", "title": "Module project"},
        ).get_json()["data"]["id"]

        response = client.post(
            f"/v1/projects/{project_id}/modules",
            json={"name": "飞行显示"},
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json()["data"], {"name": "飞行显示"})
        detail = client.get(f"/v1/projects/{project_id}").get_json()["data"]
        self.assertEqual(detail["modules"], ["飞行显示"])
        self.assertEqual(detail["requirements"], [])

    def test_create_module_rejects_duplicate_names(self):
        client = self._client()
        project_id = client.post(
            "/v1/projects",
            json={"code": "PRJ-DUP", "title": "Duplicate module project"},
        ).get_json()["data"]["id"]
        client.post(f"/v1/projects/{project_id}/modules", json={"name": "认证"})

        response = client.post(
            f"/v1/projects/{project_id}/modules",
            json={"name": "认证"},
        )

        self.assertEqual(response.status_code, 409)

    def test_create_module_rejects_missing_name(self):
        client = self._client()
        project_id = client.post(
            "/v1/projects",
            json={"code": "PRJ-EMPTY", "title": "Empty module project"},
        ).get_json()["data"]["id"]

        response = client.post(f"/v1/projects/{project_id}/modules", json={"name": " "})

        self.assertEqual(response.status_code, 400)


if __name__ == "__main__":
    unittest.main()
