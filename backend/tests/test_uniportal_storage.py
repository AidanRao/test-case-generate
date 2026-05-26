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

    def _write_requirements(
        self,
        portal_project_id,
        item_id,
        code,
        project_name=None,
        title="Show wind",
        content="Show valid wind values.",
        requirement_id=None,
    ):
        item_dir = os.path.join(self.shared.name, portal_project_id, item_id)
        source_dir = (
            os.path.join(item_dir, project_name) if project_name else item_dir
        )
        os.makedirs(source_dir, exist_ok=True)
        requirement = {
            "title": title,
            "type": "Functional",
            "code": code,
            "content": content,
        }
        if requirement_id:
            requirement["id"] = requirement_id
        with open(os.path.join(source_dir, "requirements.json"), "w", encoding="utf-8") as output:
            json.dump(
                [
                    {
                        "module": "Display",
                        "requirements": [requirement],
                    }
                ],
                output,
            )

    def test_no_portal_context_lists_only_local_projects(self):
        storage = JsonStorage(self.local.name, self.shared.name)
        local_id = storage.create_project({"code": "LOCAL-001", "title": "Local"})

        projects = storage.list_projects()
        self.assertEqual(projects, [{"id": local_id, "code": "LOCAL-001", "title": "Local", "source": "local"}])

    def test_portal_context_query_lists_synced_projects_without_triggering_sync(self):
        sibling_item_id = "item-003"
        self._write_requirements(
            "portal-001", sibling_item_id, "REQ-003", "sibling-source"
        )
        storage = JsonStorage(self.local.name, self.shared.name)
        storage.create_project({"code": "LOCAL-001", "title": "Local"})

        with patch.object(storage, "synchronize_uniportal") as sync:
            self.assertEqual(storage.list_projects(portal_project_id="portal-001"), [])
        sync.assert_not_called()

        storage.synchronize_uniportal()
        projects = storage.list_projects(portal_project_id="portal-001")

        self.assertEqual({item["code"] for item in projects}, {self.item_id, sibling_item_id})
        self.assertTrue(all(item["source"] == "uniportal" for item in projects))
        self.assertNotIn(self.other_item_id, {item["code"] for item in projects})
        self.assertNotIn("LOCAL-001", {item["code"] for item in projects})

    def test_imports_scoped_portal_project_and_stores_requirements_locally(self):
        storage = JsonStorage(self.local.name, self.shared.name)

        storage.synchronize_uniportal()
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
            self.assertEqual(len(json.load(source)), 2)
        with open(os.path.join(self.local.name, "uniportal_sync.json"), "r", encoding="utf-8") as source:
            mapping = json.load(source)["projects"]
        self.assertIn(
            {
                "project_id": project_id,
                "project_code": self.item_id,
                "portal_project_id": "portal-001",
                "source_path": os.path.abspath(self.shared.name),
            },
            mapping,
        )

    def test_repeated_sync_reuses_generated_project_id(self):
        storage = JsonStorage(self.local.name, self.shared.name)
        storage.synchronize_uniportal()
        first = storage.list_projects(portal_project_id="portal-001")[0]
        self._write_requirements(
            "portal-001", self.item_id, "REQ-UPDATED", self.project_name
        )

        storage.synchronize_uniportal()
        second = storage.list_projects(portal_project_id="portal-001")[0]
        self.assertEqual(second["id"], first["id"])
        self.assertEqual(
            storage.list_requirements(first["id"])[0]["code"], "REQ-UPDATED"
        )

    def test_repeated_sync_updates_matching_requirement_code_and_reuses_id(self):
        storage = JsonStorage(self.local.name, self.shared.name)
        storage.synchronize_uniportal()
        project = storage.list_projects(portal_project_id="portal-001")[0]
        first = storage.list_requirements(project["id"])[0]
        storage.add_testcases(
            project["id"],
            first["id"],
            [
                {
                    "id": "TC-001",
                    "requirement_code": first["code"],
                    "title": "Existing testcase",
                    "code": "TC-001",
                    "type": "Functional",
                    "test_steps": [],
                }
            ],
        )
        self._write_requirements(
            "portal-001",
            self.item_id,
            "REQ-001",
            self.project_name,
            title="Show updated wind",
            content="Show updated wind values.",
            requirement_id="incoming-replacement-id",
        )

        storage.synchronize_uniportal()
        updated = storage.list_requirements(project["id"])[0]

        self.assertEqual(updated["id"], first["id"])
        self.assertEqual(updated["title"], "Show updated wind")
        self.assertEqual(updated["content"], "Show updated wind values.")
        self.assertEqual(len(storage.list_testcases(project["id"], first["id"])), 1)

    def test_sync_without_changes_does_not_write_local_storage(self):
        storage = JsonStorage(self.local.name, self.shared.name)
        storage.synchronize_uniportal()
        project = storage.list_projects(portal_project_id="portal-001")[0]

        with (
            patch.object(storage.io, "save", wraps=storage.io.save) as save,
            patch("builtins.print") as output,
        ):
            storage.synchronize_uniportal()

        save.assert_not_called()
        output.assert_not_called()
        self.assertEqual(
            storage.list_projects(portal_project_id="portal-001")[0]["id"],
            project["id"],
        )

    def test_sync_logs_only_files_written_for_new_project(self):
        storage = JsonStorage(self.local.name, self.shared.name)

        with patch("builtins.print") as output:
            storage.synchronize_uniportal()

        messages = [call.args[0] for call in output.call_args_list]
        self.assertTrue(any("wrote projects.json: created" in item for item in messages))
        self.assertTrue(any("wrote requirements.json: synchronized" in item for item in messages))
        self.assertTrue(any("wrote uniportal_sync.json: updated" in item for item in messages))
        self.assertFalse(any("testcases.json" in item for item in messages))

    def test_sync_logs_each_file_written_when_project_is_removed(self):
        storage = JsonStorage(self.local.name, self.shared.name)
        storage.synchronize_uniportal()
        project = storage.list_projects(portal_project_id="portal-001")[0]
        requirement = storage.list_requirements(project["id"])[0]
        storage.add_testcases(
            project["id"],
            requirement["id"],
            [{"id": "TC-001", "code": "TC-001", "title": "Existing testcase"}],
        )
        os.remove(
            os.path.join(
                self.shared.name,
                "portal-001",
                self.item_id,
                self.project_name,
                "requirements.json",
            )
        )

        with patch("builtins.print") as output:
            storage.synchronize_uniportal()

        messages = [call.args[0] for call in output.call_args_list]
        self.assertTrue(any("wrote projects.json: deleted" in item for item in messages))
        self.assertTrue(any("wrote requirements.json: deleted" in item for item in messages))
        self.assertTrue(any("wrote testcases.json: deleted" in item for item in messages))
        self.assertTrue(any("wrote uniportal_sync.json: updated" in item for item in messages))

    def test_distinct_uniportal_sources_do_not_delete_each_others_projects(self):
        other_source = tempfile.TemporaryDirectory()
        self.addCleanup(other_source.cleanup)
        other_item_id = "item-other-source"
        item_dir = os.path.join(other_source.name, "portal-other", other_item_id, "other")
        os.makedirs(item_dir, exist_ok=True)
        with open(os.path.join(item_dir, "requirements.json"), "w", encoding="utf-8") as output:
            json.dump(
                [{"module": "Other", "requirements": [{"code": "REQ-OTHER"}]}],
                output,
            )
        first_source = JsonStorage(self.local.name, self.shared.name)
        second_source = JsonStorage(self.local.name, other_source.name)

        first_source.synchronize_uniportal()
        first_ids = {
            item["code"]: item["id"] for item in first_source.project_store.list_projects()
        }
        second_source.synchronize_uniportal()
        second_project = second_source.list_projects(portal_project_id="portal-other")[0]
        first_source.synchronize_uniportal()
        second_source.synchronize_uniportal()

        projects = first_source.project_store.list_projects()
        self.assertEqual(
            {item["code"]: item["id"] for item in projects},
            {
                **first_ids,
                other_item_id: second_project["id"],
            },
        )
        self.assertEqual(
            {item["source_path"] for item in first_source._load_sync_entries()},
            {os.path.abspath(self.shared.name), os.path.abspath(other_source.name)},
        )

    def test_sync_updates_existing_project_with_same_code_instead_of_creating_one(self):
        storage = JsonStorage(self.local.name, self.shared.name)
        local_id = storage.create_project({"code": self.item_id, "title": "Local"})

        storage.synchronize_uniportal()
        imported = storage.list_projects(portal_project_id="portal-001")[0]
        projects = storage.list_projects()
        self.assertEqual(imported["id"], local_id)
        self.assertEqual(imported["title"], self.project_name)
        self.assertEqual(imported["code"], self.item_id)
        self.assertEqual(imported["source"], "uniportal")
        self.assertEqual(projects, [])
        self.assertTrue(storage.is_read_only_project(local_id))
        self.assertEqual(storage.list_requirements(local_id)[0]["code"], "REQ-001")

    def test_flat_legacy_item_uses_item_id_as_project_name_fallback(self):
        legacy_item_id = "item-legacy"
        self._write_requirements("portal-legacy", legacy_item_id, "REQ-LEGACY")
        storage = JsonStorage(self.local.name, self.shared.name)

        storage.synchronize_uniportal()
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
            app.config["STORAGE"].synchronize_uniportal()
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
