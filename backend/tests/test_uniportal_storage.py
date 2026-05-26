import json
import os
import tempfile
import unittest
from unittest.mock import patch

from app.storage.json_storage import JsonStorage


class UniPortalStorageTest(unittest.TestCase):
    def setUp(self):
        self.local = tempfile.TemporaryDirectory()
        self.shared = tempfile.TemporaryDirectory()
        self.addCleanup(self.local.cleanup)
        self.addCleanup(self.shared.cleanup)
        self.item_id = "item-001"
        self.other_item_id = "item-002"
        self.project_name = "wind-display-source"
        self.other_project_name = "cabin-pressure-source"
        self._write_requirements(
            "portal-001", self.item_id, "REQ-001", self.project_name
        )
        self._write_requirements(
            "portal-002", self.other_item_id, "REQ-002", self.other_project_name
        )

    def _write_requirements(self, portal_project_id, item_id, code, project_name=None):
        item_dir = os.path.join(self.shared.name, portal_project_id, item_id)
        source_dir = (
            os.path.join(item_dir, project_name) if project_name else item_dir
        )
        os.makedirs(source_dir, exist_ok=True)
        with open(os.path.join(source_dir, "requirements.json"), "w", encoding="utf-8") as output:
            json.dump(
                [
                    {
                        "module": "Display",
                        "requirements": [
                            {
                                "title": "Show wind",
                                "type": "Functional",
                                "code": code,
                                "content": "Show valid wind values.",
                            }
                        ],
                    }
                ],
                output,
            )

    def test_no_portal_context_lists_only_local_projects(self):
        storage = JsonStorage(self.local.name, self.shared.name)
        local_id = storage.create_project({"code": "LOCAL-001", "title": "Local"})

        projects = storage.list_projects()
        self.assertEqual(projects, [{"id": local_id, "code": "LOCAL-001", "title": "Local", "source": "local"}])

    def test_portal_context_lists_only_projects_in_that_portal_project(self):
        sibling_item_id = "item-003"
        self._write_requirements(
            "portal-001", sibling_item_id, "REQ-003", "sibling-source"
        )
        storage = JsonStorage(self.local.name, self.shared.name)
        storage.create_project({"code": "LOCAL-001", "title": "Local"})

        projects = storage.list_projects(portal_project_id="portal-001")

        self.assertEqual({item["code"] for item in projects}, {self.item_id, sibling_item_id})
        self.assertTrue(all(item["source"] == "uniportal" for item in projects))
        self.assertNotIn(self.other_item_id, {item["code"] for item in projects})
        self.assertNotIn("LOCAL-001", {item["code"] for item in projects})

    def test_imports_scoped_portal_project_and_stores_requirements_locally(self):
        storage = JsonStorage(self.local.name, self.shared.name)

        project = storage.list_projects(portal_project_id="portal-001")[0]
        self.assertIsNotNone(project)
        self.assertNotEqual(project["id"], self.item_id)
        self.assertEqual(project["code"], self.item_id)
        self.assertEqual(project["title"], self.project_name)
        self.assertEqual(project["source"], "uniportal")
        self.assertTrue(storage.is_read_only_project(project["id"]))

        project_id = project["id"]
        requirements = storage.list_requirements(project_id)
        self.assertEqual(len(requirements), 1)
        self.assertEqual(requirements[0]["project_id"], project_id)
        self.assertEqual(requirements[0]["code"], "REQ-001")
        self.assertTrue(requirements[0]["id"])
        self.assertEqual(
            storage.get_project_counts([project_id])[project_id]["requirement_count"],
            1,
        )

        with open(os.path.join(self.local.name, "requirements.json"), "r", encoding="utf-8") as source:
            self.assertEqual(len(json.load(source)), 1)
        with open(os.path.join(self.local.name, "uniportal_sync.json"), "r", encoding="utf-8") as source:
            mapping = json.load(source)["projects"]
        self.assertEqual(
            mapping,
            [{
                "project_id": project_id,
                "project_code": self.item_id,
                "portal_project_id": "portal-001",
            }],
        )

    def test_repeated_sync_reuses_generated_project_id(self):
        storage = JsonStorage(self.local.name, self.shared.name)
        first = storage.list_projects(portal_project_id="portal-001")[0]
        self._write_requirements(
            "portal-001", self.item_id, "REQ-UPDATED", self.project_name
        )

        second = storage.list_projects(portal_project_id="portal-001")[0]
        self.assertEqual(second["id"], first["id"])
        self.assertEqual(
            storage.list_requirements(first["id"])[0]["code"], "REQ-UPDATED"
        )

    def test_sync_does_not_take_over_local_project_with_same_code(self):
        storage = JsonStorage(self.local.name, self.shared.name)
        local_id = storage.create_project({"code": self.item_id, "title": "Local"})

        imported = storage.list_projects(portal_project_id="portal-001")[0]
        projects = storage.list_projects()
        self.assertEqual(projects, [{"id": local_id, "code": self.item_id, "title": "Local", "source": "local"}])
        self.assertEqual(imported["code"], self.item_id)
        self.assertEqual(imported["source"], "uniportal")

    def test_flat_legacy_item_uses_item_id_as_project_name_fallback(self):
        legacy_item_id = "item-legacy"
        self._write_requirements("portal-legacy", legacy_item_id, "REQ-LEGACY")
        storage = JsonStorage(self.local.name, self.shared.name)

        project = storage.list_projects(portal_project_id="portal-legacy")[0]

        self.assertEqual(project["code"], legacy_item_id)
        self.assertEqual(project["title"], legacy_item_id)

    def test_api_rejects_writes_to_uniportal_requirements(self):
        with patch.dict(
            os.environ,
            {
                "DATA_DIR": self.local.name,
                "UNIPORTAL_STORAGE_PATH": self.shared.name,
            },
            clear=False,
        ):
            from app import create_app

            app = create_app()
            app.testing = True
            client = app.test_client()
            local_id = client.post(
                "/v1/projects",
                json={"code": "LOCAL-001", "title": "Local", "requirements": []},
            ).get_json()["data"]["id"]
            no_context = client.get("/v1/projects").get_json()["data"]["list"]
            portal_one = client.get(
                "/v1/projects?portal_project_id=portal-001"
            ).get_json()["data"]["list"]
            portal_two = client.get(
                "/v1/projects?portal_project_id=portal-002"
            ).get_json()["data"]["list"]
            self.assertEqual(
                {item["code"] for item in no_context},
                {"LOCAL-001"},
            )
            self.assertEqual(no_context[0]["id"], local_id)
            self.assertEqual(no_context[0]["source"], "local")
            self.assertEqual({item["code"] for item in portal_one}, {self.item_id})
            self.assertEqual({item["code"] for item in portal_two}, {self.other_item_id})
            self.assertEqual(portal_one[0]["source"], "uniportal")
            self.assertNotIn("read_only", portal_one[0])
            response = client.put(
                f"/v1/projects/{portal_one[0]['id']}/requirements/missing",
                json={"title": "Changed"},
            )
            self.assertEqual(response.status_code, 403)


if __name__ == "__main__":
    unittest.main()
