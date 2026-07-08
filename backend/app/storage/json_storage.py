import os
from copy import deepcopy

from app.storage.base import StorageBackend
from app.storage.json_io import JsonIO
from app.storage.project_store import ProjectStore
from app.storage.requirement_store import RequirementStore
from app.storage.testcase_store import TestCaseStore
from app.storage.ai_config_store import AIConfigStore
from app.storage.project_sources import (
    LOCAL_SOURCE,
    UNIPORTAL_SOURCE,
)
from app.storage.quality_store import QualityStore
from app.storage.system_task_store import SystemTaskStore
from app.storage.uniportal_source import UniPortalRequirementSource


class JsonStorage(StorageBackend):
    UNIPORTAL_SYNC_TASK_ID = "uniportal_sync"

    def __init__(
        self,
        data_dir,
        uniportal_storage_path=None,
        uniportal_sync_enabled=True,
        uniportal_sync_interval_seconds=300,
    ):
        self.data_dir = data_dir
        os.makedirs(self.data_dir, exist_ok=True)
        io = JsonIO(self.data_dir)
        self.io = io
        self._sync_lock = None
        self.uniportal_sync_path = os.path.join(self.data_dir, "uniportal_sync.json")
        self.project_store = ProjectStore(
            io, os.path.join(self.data_dir, "projects.json")
        )
        self.testcase_store = TestCaseStore(
            io, os.path.join(self.data_dir, "testcases.json")
        )
        self.quality_store = QualityStore(
            io, os.path.join(self.data_dir, "quality.json")
        )
        self.requirement_store = RequirementStore(
            io, os.path.join(self.data_dir, "requirements.json"), self.project_store
        )
        self.ai_config_store = AIConfigStore(
            io, os.path.join(self.data_dir, "ai_config.json")
        )
        self.system_task_store = SystemTaskStore(
            io, os.path.join(self.data_dir, "system_tasks.json")
        )
        self.uniportal_source = UniPortalRequirementSource(uniportal_storage_path)

    def _load_sync_entries(self):
        state = self.io.load(self.uniportal_sync_path, {"projects": []})
        projects = state.get("projects", []) if isinstance(state, dict) else []
        return [item for item in projects if isinstance(item, dict)]

    def _log_uniportal_write(self, filename, action):
        print(
            f"[UniPortal sync] source_path={self.uniportal_source.storage_path} "
            f"wrote {filename}: {action}",
            flush=True,
        )

    def _save_sync_entries(self, entries):
        current = self._load_sync_entries()
        key = lambda item: (
            str(item.get("source_path", "")),
            str(item.get("project_code", "")),
            str(item.get("portal_project_id", "")),
            str(item.get("project_id", "")),
        )
        if sorted(current, key=key) == sorted(entries, key=key):
            return False
        self.io.save(self.uniportal_sync_path, {"projects": entries})
        self._log_uniportal_write(
            "uniportal_sync.json", f"updated mapping entries={len(entries)}"
        )
        return True

    def _sync_entries_by_project_id(self):
        return {
            str(item.get("project_id")): item
            for item in self._load_sync_entries()
            if item.get("project_id")
        }

    def _project_source(self, project_id, entries_by_project_id=None):
        entries = (
            entries_by_project_id
            if entries_by_project_id is not None
            else self._sync_entries_by_project_id()
        )
        if str(project_id) in entries:
            return UNIPORTAL_SOURCE
        return LOCAL_SOURCE

    def _decorate_project(self, project, entries_by_project_id=None):
        source = self._project_source(project.get("id"), entries_by_project_id)
        return {**project, "source": source.name}

    def _project_by_code(self, project_code):
        for project in self.project_store.list_projects():
            if str(project.get("code")) == str(project_code):
                return project
        return None

    def synchronize_uniportal(self):
        if not self.uniportal_source.enabled:
            return
        remote_projects = self.uniportal_source.discover_projects()
        entries = self._load_sync_entries()
        source_path = self.uniportal_source.storage_path
        entries_by_code = {
            str(item.get("project_code")): item
            for item in entries
            if item.get("project_code")
            and (
                not item.get("source_path")
                or item.get("source_path") == source_path
            )
        }
        seen_codes = set()
        updated_entries = []
        for remote in remote_projects:
            project_code = str(remote["code"])
            seen_codes.add(project_code)
            entry = entries_by_code.get(project_code)
            local_project = None
            if entry:
                project = self.project_store.get_project(entry.get("project_id"))
                local_project = project.to_dict() if project else None
            if local_project is None:
                local_project = self._project_by_code(project_code)
            if local_project is None:
                local_project_id = self.project_store.create_project(
                    {"code": project_code, "title": remote["title"]}
                )
                self._log_uniportal_write(
                    "projects.json",
                    f"created project_code={project_code} project_id={local_project_id}",
                )
            else:
                local_project_id = local_project["id"]
                if (
                    local_project.get("code") != project_code
                    or local_project.get("title") != remote["title"]
                ):
                    self.project_store.update_project(
                        local_project_id,
                        {"code": project_code, "title": remote["title"]},
                    )
                    self._log_uniportal_write(
                        "projects.json",
                        f"updated project_code={project_code} project_id={local_project_id}",
                    )
            requirements = self.uniportal_source.list_requirements(project_code) or []
            if self.requirement_store.replace_by_project(
                local_project_id, requirements
            ):
                self._log_uniportal_write(
                    "requirements.json",
                    f"synchronized project_code={project_code} project_id={local_project_id}",
                )
            updated_entries.append(
                {
                    "project_id": str(local_project_id),
                    "project_code": project_code,
                    "portal_project_id": remote["portal_project_id"],
                    "source_path": source_path,
                }
            )

        for entry in entries:
            project_code = str(entry.get("project_code", ""))
            entry_source_path = entry.get("source_path")
            is_current_source = entry_source_path == source_path
            if (
                (is_current_source or not entry_source_path)
                and project_code in seen_codes
            ):
                continue
            if not is_current_source:
                updated_entries.append(entry)
                continue
            project_id = entry.get("project_id")
            if self.project_store.delete_project(project_id):
                self._log_uniportal_write(
                    "projects.json",
                    f"deleted project_code={project_code} project_id={project_id}",
                )
            if self.requirement_store.delete_by_project(project_id):
                self._log_uniportal_write(
                    "requirements.json",
                    f"deleted project_code={project_code} project_id={project_id}",
                )
            if self.testcase_store.delete_by_project(project_id):
                self._log_uniportal_write(
                    "testcases.json",
                    f"deleted project_code={project_code} project_id={project_id}",
                )
            self.quality_store.delete_by_project(project_id)
        self._save_sync_entries(updated_entries)

    def _task_runtime(self, task, scheduler=None):
        available = self.uniportal_source.enabled
        running = False
        if scheduler is not None:
            job = scheduler.get_job(task.get("id"))
            if job is not None:
                next_run = getattr(job, 'next_run_time', None)
                running = bool(next_run is not None)
        return {**task, "available": available, "running": running}

    def list_system_tasks(self, scheduler=None):
        return [
            self._task_runtime(task, scheduler)
            for task in self.system_task_store.list_tasks()
        ]

    def save_system_task(self, task_id, payload, scheduler=None):
        task = self.system_task_store.save_task(task_id, payload)
        if task is None:
            return None
        if scheduler is not None:
            from app.scheduler import update_job
            update_job(scheduler, task)
        return self._task_runtime(task, scheduler)

    def run_system_task(self, task_id, scheduler=None):
        task = self.system_task_store.get_task(task_id)
        if task is None or task_id != self.UNIPORTAL_SYNC_TASK_ID:
            return None
        self.synchronize_uniportal()
        return self._task_runtime(task, scheduler)

    def list_projects(self, keyword=None, portal_project_id=None):
        entries_by_project_id = self._sync_entries_by_project_id()
        portal_project_ids = {
            str(item.get("project_id"))
            for item in entries_by_project_id.values()
            if item.get("portal_project_id") == portal_project_id
            and (
                not item.get("source_path")
                or item.get("source_path") == self.uniportal_source.storage_path
            )
        }
        projects = []
        for project in self.project_store.list_projects(keyword):
            source = self._project_source(project.get("id"), entries_by_project_id)
            if portal_project_id:
                if str(project.get("id")) not in portal_project_ids:
                    continue
            elif source.name != LOCAL_SOURCE.name:
                continue
            projects.append({**project, "source": source.name})
        return projects

    def get_project_counts(self, project_ids):
        return self.requirement_store.get_project_counts(project_ids)

    def get_project(self, project_id):
        project = self.project_store.get_project(project_id)
        if project:
            return self._decorate_project(project.to_dict())
        return None

    def project_code_exists(self, code, exclude_project_id=None):
        for project in self.project_store.list_projects():
            if exclude_project_id is not None and str(project["id"]) == str(exclude_project_id):
                continue
            if project.get("code") == code:
                return True
        return False

    def create_project(self, payload):
        return self.project_store.create_project(payload)

    def update_project(self, project_id, payload):
        return self.project_store.update_project(project_id, payload)

    def delete_project(self, project_id):
        deleted = self.project_store.delete_project(project_id)
        if deleted:
            self.requirement_store.delete_by_project(project_id)
            self.testcase_store.delete_by_project(project_id)
            self.quality_store.delete_by_project(project_id)
        return deleted

    def list_requirements(self, project_id, module=None, req_type=None, keyword=None):
        return self.requirement_store.list_requirements(project_id, module, req_type, keyword)

    def get_requirement(self, project_id, requirement_id):
        return self.requirement_store.get_requirement(project_id, requirement_id)

    def is_read_only_project(self, project_id):
        return self._project_source(project_id).read_only

    def update_requirement(self, project_id, requirement_id, payload):
        return self.requirement_store.update_requirement(project_id, requirement_id, payload)

    def complete_requirements(self, project_id, requirements, scope):
        return self.requirement_store.complete_requirements(project_id, requirements, scope)

    def create_requirement(self, project_id, payload):
        return self.requirement_store.create_requirement(project_id, payload)

    def delete_requirement(self, project_id, requirement_id):
        return self.requirement_store.delete_requirement(project_id, requirement_id, self.testcase_store)

    def list_testcases(self, project_id, requirement_id):
        return self.testcase_store.list_testcases(project_id, requirement_id)

    def list_project_testcases(self, project_id):
        return self.testcase_store.list_project_testcases(project_id)

    def get_project_quality(self, project_id):
        return self.quality_store.get_quality(project_id)

    def save_project_quality(self, project_id, payload):
        return self.quality_store.save_quality(project_id, payload)

    def add_testcases(self, project_id, requirement_id, testcases):
        return self.testcase_store.add_testcases(project_id, requirement_id, testcases)

    def update_testcase(self, project_id, testcase_id, payload):
        return self.testcase_store.update_testcase(project_id, testcase_id, payload)

    def delete_testcase(self, project_id, testcase_id):
        return self.testcase_store.delete_testcase(project_id, testcase_id)

    def delete_testcases_by_requirement(self, project_id, requirement_id):
        return self.testcase_store.delete_testcases_by_requirement(project_id, requirement_id)

    def get_ai_config(self):
        config = self.ai_config_store.get_config()
        return config.to_dict() if config else None

    def save_ai_config(self, payload):
        config = self.ai_config_store.save_config(payload)
        return config.to_dict() if config else None
