import json
import os
import shutil
import tempfile
import unittest
from unittest.mock import patch

from app.storage.json_storage import JsonStorage


REQUIREMENT_PATH = "document-validator/requirement.json"


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
    ):
        item_dir = os.path.join(self.shared.name, portal_project_id, item_id)
        os.makedirs(item_dir, exist_ok=True)
        self._write_project_manifest(item_dir, project_name or "source")
        validator_dir = os.path.join(item_dir, "document-validator")
        os.makedirs(validator_dir, exist_ok=True)
        self._write_document_validator_file(
            validator_dir,
            [
                {
                    "id": code,
                    "title": title,
                    "type": "功能需求",
                    "level": 2,
                    "parent_id": "module",
                    "is_req": 1,
                    "content": content,
                    "tables": [],
                }
            ],
        )

    def _write_project_manifest(self, item_dir, project_name):
        manifest_dir = os.path.join(item_dir, "uniportal")
        os.makedirs(manifest_dir, exist_ok=True)
        with open(
            os.path.join(manifest_dir, "project_manifest.json"),
            "w",
            encoding="utf-8",
        ) as output:
            json.dump({"current_item": {"name": project_name}}, output)

    def _project_manifest_path(self, portal_project_id, item_id):
        return os.path.join(
            self.shared.name,
            portal_project_id,
            item_id,
            "uniportal",
            "project_manifest.json",
        )

    def _write_document_validator_file(self, validator_dir, requirements):
        os.makedirs(validator_dir, exist_ok=True)
        payload = [
            {
                "id": "root",
                "title": "Root",
                "level": 0,
                "parent_id": "root",
                "is_req": 0,
                "content": None,
                "tables": [],
            },
            {
                "id": "module",
                "title": "Display",
                "level": 1,
                "parent_id": "root",
                "is_req": 0,
                "content": None,
                "tables": [],
            },
            *requirements,
        ]
        with open(
            os.path.join(validator_dir, "requirement.json"),
            "w",
            encoding="utf-8",
        ) as output:
            json.dump(payload, output)

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

        storage.synchronize_uniportal(REQUIREMENT_PATH)
        projects = storage.list_projects(portal_project_id="portal-001")

        self.assertEqual({item["code"] for item in projects}, {self.item_id, sibling_item_id})
        self.assertTrue(all(item["source"] == "uniportal" for item in projects))
        self.assertNotIn(self.other_item_id, {item["code"] for item in projects})
        self.assertNotIn("LOCAL-001", {item["code"] for item in projects})

    def test_imports_scoped_portal_project_and_stores_requirements_locally(self):
        storage = JsonStorage(self.local.name, self.shared.name)

        storage.synchronize_uniportal(REQUIREMENT_PATH)
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

    def test_reads_project_name_from_manifest_instead_of_sibling_directories(self):
        item_dir = os.path.join(
            self.shared.name,
            "portal-001",
            self.item_id,
        )
        os.makedirs(os.path.join(item_dir, "aaa-wrong-project", "src"))
        storage = JsonStorage(self.local.name, self.shared.name)

        storage.synchronize_uniportal(REQUIREMENT_PATH)

        project = storage.list_projects(portal_project_id="portal-001")[0]
        self.assertEqual(project["title"], self.project_name)

    def test_sync_updates_project_title_when_manifest_name_changes(self):
        storage = JsonStorage(self.local.name, self.shared.name)
        storage.synchronize_uniportal(REQUIREMENT_PATH)
        project = storage.list_projects(portal_project_id="portal-001")[0]
        item_dir = os.path.join(
            self.shared.name,
            "portal-001",
            self.item_id,
        )
        self._write_project_manifest(item_dir, "  Updated project name  ")

        storage.synchronize_uniportal(REQUIREMENT_PATH)

        updated = storage.list_projects(portal_project_id="portal-001")[0]
        self.assertEqual(updated["id"], project["id"])
        self.assertEqual(updated["title"], "Updated project name")

    def test_invalid_manifests_do_not_import_new_projects(self):
        invalid_manifests = {
            "missing": None,
            "invalid-json": "{",
            "missing-current-item": {},
            "invalid-current-item": {"current_item": "invalid"},
            "missing-name": {"current_item": {}},
            "non-string-name": {"current_item": {"name": 123}},
            "empty-name": {"current_item": {"name": "   "}},
        }
        for suffix, manifest in invalid_manifests.items():
            item_id = f"item-{suffix}"
            self._write_requirements(
                "portal-invalid",
                item_id,
                f"REQ-{suffix}",
                f"project-{suffix}",
            )
            manifest_path = self._project_manifest_path("portal-invalid", item_id)
            if manifest is None:
                os.remove(manifest_path)
            elif isinstance(manifest, str):
                with open(manifest_path, "w", encoding="utf-8") as output:
                    output.write(manifest)
            else:
                with open(manifest_path, "w", encoding="utf-8") as output:
                    json.dump(manifest, output)
        storage = JsonStorage(self.local.name, self.shared.name)

        storage.synchronize_uniportal(REQUIREMENT_PATH)

        self.assertEqual(
            storage.list_projects(portal_project_id="portal-invalid"),
            [],
        )

    def test_manifest_error_preserves_existing_synced_data_and_mapping(self):
        storage = JsonStorage(self.local.name, self.shared.name)
        storage.synchronize_uniportal(REQUIREMENT_PATH)
        project = storage.list_projects(portal_project_id="portal-001")[0]
        requirement = storage.list_requirements(project["id"])[0]
        storage.add_testcases(
            project["id"],
            requirement["id"],
            [
                {
                    "id": "TC-PRESERVED",
                    "requirement_code": requirement["code"],
                    "title": "Preserved testcase",
                    "code": "TC-PRESERVED",
                    "type": "Functional",
                    "scenario_type": "正常流程用例",
                    "test_steps": [],
                }
            ],
        )
        mapping = storage._load_sync_entries()
        manifest_path = self._project_manifest_path("portal-001", self.item_id)
        with open(manifest_path, "w", encoding="utf-8") as output:
            output.write("{")

        with (
            patch.object(storage.io, "save", wraps=storage.io.save) as save,
            patch("builtins.print") as output,
        ):
            storage.synchronize_uniportal(REQUIREMENT_PATH)

        save.assert_not_called()
        output.assert_not_called()
        preserved = storage.get_project(project["id"])
        self.assertIsNotNone(preserved)
        self.assertIn(
            project["id"],
            {
                item["id"]
                for item in storage.list_projects(portal_project_id="portal-001")
            },
        )
        self.assertEqual(storage.list_requirements(project["id"]), [requirement])
        self.assertEqual(
            [
                item["id"]
                for item in storage.list_testcases(
                    project["id"],
                    requirement["id"],
                )
            ],
            ["TC-PRESERVED"],
        )
        self.assertEqual(storage._load_sync_entries(), mapping)

    def test_missing_manifest_preserves_existing_item_when_requirements_are_missing(self):
        storage = JsonStorage(self.local.name, self.shared.name)
        storage.synchronize_uniportal(REQUIREMENT_PATH)
        project = storage.list_projects(portal_project_id="portal-001")[0]
        requirements = storage.list_requirements(project["id"])
        mapping = storage._load_sync_entries()
        os.remove(self._project_manifest_path("portal-001", self.item_id))
        os.remove(
            os.path.join(
                self.shared.name,
                "portal-001",
                self.item_id,
                REQUIREMENT_PATH,
            )
        )

        storage.synchronize_uniportal(REQUIREMENT_PATH)

        preserved = storage.get_project(project["id"])
        self.assertIsNotNone(preserved)
        self.assertIn(
            project["id"],
            {
                item["id"]
                for item in storage.list_projects(portal_project_id="portal-001")
            },
        )
        self.assertEqual(storage.list_requirements(project["id"]), requirements)
        self.assertEqual(storage._load_sync_entries(), mapping)

    def test_repeated_sync_reuses_generated_project_id(self):
        storage = JsonStorage(self.local.name, self.shared.name)
        storage.synchronize_uniportal(REQUIREMENT_PATH)
        first = storage.list_projects(portal_project_id="portal-001")[0]
        self._write_requirements(
            "portal-001", self.item_id, "REQ-UPDATED", self.project_name
        )

        storage.synchronize_uniportal(REQUIREMENT_PATH)
        second = storage.list_projects(portal_project_id="portal-001")[0]
        self.assertEqual(second["id"], first["id"])
        self.assertEqual(
            storage.list_requirements(first["id"])[0]["code"], "REQ-UPDATED"
        )

    def test_repeated_sync_updates_matching_requirement_code_and_reuses_id(self):
        storage = JsonStorage(self.local.name, self.shared.name)
        storage.synchronize_uniportal(REQUIREMENT_PATH)
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
                    "scenario_type": "正常流程用例",
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
        )

        storage.synchronize_uniportal(REQUIREMENT_PATH)
        updated = storage.list_requirements(project["id"])[0]

        self.assertEqual(updated["id"], first["id"])
        self.assertEqual(updated["title"], "Show updated wind")
        self.assertEqual(updated["content"], "Show updated wind values.")
        self.assertEqual(len(storage.list_testcases(project["id"], first["id"])), 1)

    def test_sync_without_changes_does_not_write_local_storage(self):
        storage = JsonStorage(self.local.name, self.shared.name)
        storage.synchronize_uniportal(REQUIREMENT_PATH)
        project = storage.list_projects(portal_project_id="portal-001")[0]

        with (
            patch.object(storage.io, "save", wraps=storage.io.save) as save,
            patch("builtins.print") as output,
        ):
            storage.synchronize_uniportal(REQUIREMENT_PATH)

        save.assert_not_called()
        output.assert_not_called()
        self.assertEqual(
            storage.list_projects(portal_project_id="portal-001")[0]["id"],
            project["id"],
        )

    def test_sync_logs_only_files_written_for_new_project(self):
        storage = JsonStorage(self.local.name, self.shared.name)

        with patch("builtins.print") as output:
            storage.synchronize_uniportal(REQUIREMENT_PATH)

        messages = [call.args[0] for call in output.call_args_list]
        self.assertTrue(any("wrote projects.json: created" in item for item in messages))
        self.assertTrue(any("wrote requirements.json: synchronized" in item for item in messages))
        self.assertTrue(any("wrote uniportal_sync.json: updated" in item for item in messages))
        self.assertFalse(any("testcases.json" in item for item in messages))

    def test_sync_logs_each_file_written_when_project_is_removed(self):
        storage = JsonStorage(self.local.name, self.shared.name)
        storage.synchronize_uniportal(REQUIREMENT_PATH)
        project = storage.list_projects(portal_project_id="portal-001")[0]
        requirement = storage.list_requirements(project["id"])[0]
        storage.add_testcases(
            project["id"],
            requirement["id"],
            [
                {
                    "id": "TC-001",
                    "code": "TC-001",
                    "title": "Existing testcase",
                    "scenario_type": "正常流程用例",
                }
            ],
        )
        os.remove(
            os.path.join(
                self.shared.name,
                "portal-001",
                self.item_id,
                "document-validator",
                "requirement.json",
            )
        )

        with patch("builtins.print") as output:
            storage.synchronize_uniportal(REQUIREMENT_PATH)

        messages = [call.args[0] for call in output.call_args_list]
        self.assertTrue(any("wrote projects.json: deleted" in item for item in messages))
        self.assertTrue(any("wrote requirements.json: deleted" in item for item in messages))
        self.assertTrue(any("wrote testcases.json: deleted" in item for item in messages))
        self.assertTrue(any("wrote uniportal_sync.json: updated" in item for item in messages))

    def test_sync_removes_project_when_item_directory_is_deleted(self):
        storage = JsonStorage(self.local.name, self.shared.name)
        storage.synchronize_uniportal(REQUIREMENT_PATH)
        project = storage.list_projects(portal_project_id="portal-001")[0]
        shutil.rmtree(
            os.path.join(
                self.shared.name,
                "portal-001",
                self.item_id,
            )
        )

        storage.synchronize_uniportal(REQUIREMENT_PATH)

        self.assertIsNone(storage.get_project(project["id"]))
        self.assertEqual(
            storage.list_projects(portal_project_id="portal-001"),
            [],
        )

    def test_distinct_uniportal_sources_do_not_delete_each_others_projects(self):
        other_source = tempfile.TemporaryDirectory()
        self.addCleanup(other_source.cleanup)
        other_item_id = "item-other-source"
        other_item_dir = os.path.join(
            other_source.name,
            "portal-other",
            other_item_id,
        )
        self._write_project_manifest(other_item_dir, "other")
        validator_dir = os.path.join(
            other_item_dir,
            "document-validator",
        )
        self._write_document_validator_file(
            validator_dir,
            [
                {
                    "id": "REQ-OTHER",
                    "title": "Other",
                    "type": "功能需求",
                    "level": 2,
                    "parent_id": "module",
                    "is_req": 1,
                    "content": "Other requirement.",
                    "tables": [],
                }
            ],
        )
        first_source = JsonStorage(self.local.name, self.shared.name)
        second_source = JsonStorage(self.local.name, other_source.name)

        first_source.synchronize_uniportal(REQUIREMENT_PATH)
        first_ids = {
            item["code"]: item["id"] for item in first_source.project_store.list_projects()
        }
        second_source.synchronize_uniportal(REQUIREMENT_PATH)
        second_project = second_source.list_projects(portal_project_id="portal-other")[0]
        first_source.synchronize_uniportal(REQUIREMENT_PATH)
        second_source.synchronize_uniportal(REQUIREMENT_PATH)

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

        storage.synchronize_uniportal(REQUIREMENT_PATH)
        imported = storage.list_projects(portal_project_id="portal-001")[0]
        projects = storage.list_projects()
        self.assertEqual(imported["id"], local_id)
        self.assertEqual(imported["title"], self.project_name)
        self.assertEqual(imported["code"], self.item_id)
        self.assertEqual(imported["source"], "uniportal")
        self.assertEqual(projects, [])
        self.assertTrue(storage.is_read_only_project(local_id))
        self.assertEqual(storage.list_requirements(local_id)[0]["code"], "REQ-001")

    def test_ignores_requirement_without_project_manifest(self):
        item_id = "item-without-manifest"
        item_dir = os.path.join(
            self.shared.name,
            "portal-flat",
            item_id,
        )
        os.makedirs(os.path.join(item_dir, "legacy-project-name", "src"))
        validator_dir = os.path.join(
            item_dir,
            "document-validator",
        )
        self._write_document_validator_file(
            validator_dir,
            [
                {
                    "id": "REQ-FLAT",
                    "title": "Flat requirement",
                    "type": "功能需求",
                    "level": 2,
                    "parent_id": "module",
                    "is_req": 1,
                    "content": "This file is at the unsupported flat path.",
                    "tables": [],
                }
            ],
        )
        storage = JsonStorage(self.local.name, self.shared.name)

        storage.synchronize_uniportal(REQUIREMENT_PATH)

        self.assertEqual(storage.list_projects(portal_project_id="portal-flat"), [])

    def test_syncs_document_validator_requirement_with_json_type_and_parent_module(self):
        item_id = "item-document-validator"
        item_dir = os.path.join(self.shared.name, "portal-doc", item_id)
        self._write_project_manifest(item_dir, "source")
        validator_dir = os.path.join(item_dir, "document-validator")
        os.makedirs(validator_dir, exist_ok=True)
        requirement_path = os.path.join(validator_dir, "requirement.json")
        with open(requirement_path, "w", encoding="utf-8") as output:
            json.dump(
                [
                    {
                        "id": "root",
                        "title": "Root",
                        "level": 0,
                        "parent_id": "root",
                        "is_req": 0,
                        "content": None,
                        "tables": [],
                    },
                    {
                        "id": "chapter",
                        "title": "3 需求",
                        "level": 2,
                        "parent_id": "root",
                        "is_req": 0,
                        "content": None,
                        "tables": [],
                    },
                    {
                        "id": "feature-parent",
                        "title": "3.1 通信模块",
                        "level": 1,
                        "parent_id": "chapter",
                        "is_req": 0,
                        "content": None,
                        "tables": [],
                    },
                    {
                        "id": "REQ-DOC-1",
                        "title": "3.1 通信握手",
                        "type": "接口需求",
                        "level": 3,
                        "parent_id": "feature-parent",
                        "is_req": 1,
                        "content": "收到请求帧后发送采样信息。",
                        "tables": [],
                    },
                    {
                        "id": "REQ-DOC-2",
                        "title": "3.2 数据打包",
                        "type": "功能需求",
                        "level": 3,
                        "parent_id": "feature-parent",
                        "is_req": 1,
                        "content": "将补偿后的角速度编码。",
                        "tables": [
                            {
                                "caption": "打包格式",
                                "headers": ["字段", "说明"],
                                "rows": [["status", "状态字"]],
                            }
                        ],
                    },
                    {
                        "id": "note",
                        "title": "4 注释",
                        "level": 1,
                        "parent_id": "root",
                        "is_req": 0,
                        "content": "非需求节点不导入。",
                        "tables": [],
                    },
                ],
                output,
            )

        storage = JsonStorage(self.local.name, self.shared.name)

        storage.synchronize_uniportal(REQUIREMENT_PATH)
        project = storage.list_projects(portal_project_id="portal-doc")[0]
        requirements = storage.list_requirements(project["id"])

        self.assertEqual(project["title"], "source")
        self.assertEqual(
            [item["code"] for item in requirements],
            ["REQ-DOC-1", "REQ-DOC-2"],
        )
        self.assertEqual(
            [item["title"] for item in requirements],
            ["3.1 通信握手", "3.2 数据打包"],
        )
        self.assertEqual(
            [item["module"] for item in requirements],
            ["3.1 通信模块", "3.1 通信模块"],
        )
        self.assertEqual(requirements[0]["type"], "接口需求")
        self.assertEqual(requirements[1]["type"], "功能需求")
        self.assertIn("收到请求帧后发送采样信息。", requirements[0]["content"])
        self.assertIn("打包格式", requirements[1]["content"])
        self.assertIn("| 字段 | 说明 |", requirements[1]["content"])
        self.assertIn("| --- | --- |", requirements[1]["content"])
        self.assertIn("| status | 状态字 |", requirements[1]["content"])

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
            client.post("/v1/system/tasks/uniportal_sync/run")
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
