import os

from app.storage.base import StorageBackend
from app.storage.json_io import JsonIO
from app.storage.project_store import ProjectStore
from app.storage.requirement_store import RequirementStore
from app.storage.testcase_store import TestCaseStore


class JsonStorage(StorageBackend):
    def __init__(self, data_dir):
        self.data_dir = data_dir
        os.makedirs(self.data_dir, exist_ok=True)
        io = JsonIO(self.data_dir)
        self.project_store = ProjectStore(io, os.path.join(self.data_dir, "projects.json"))
        self.testcase_store = TestCaseStore(io, os.path.join(self.data_dir, "testcases.json"))
        self.requirement_store = RequirementStore(
            io, os.path.join(self.data_dir, "requirements.json"), self.project_store
        )

    def list_projects(self, keyword=None):
        return self.project_store.list_projects(keyword)

    def get_project_counts(self, project_ids):
        return self.requirement_store.get_project_counts(project_ids)

    def get_project(self, project_id):
        project = self.project_store.get_project(project_id)
        return project.to_dict() if project else None

    def create_project(self, payload):
        return self.project_store.create_project(payload)

    def update_project(self, project_id, payload):
        return self.project_store.update_project(project_id, payload)

    def delete_project(self, project_id):
        deleted = self.project_store.delete_project(project_id)
        if deleted:
            self.requirement_store.delete_by_project(project_id)
            self.testcase_store.delete_by_project(project_id)
        return deleted

    def list_requirements(self, project_id, module=None, req_type=None, keyword=None):
        return self.requirement_store.list_requirements(project_id, module, req_type, keyword)

    def get_requirement(self, project_id, requirement_id):
        return self.requirement_store.get_requirement(project_id, requirement_id)

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

    def add_testcases(self, project_id, requirement_id, testcases):
        return self.testcase_store.add_testcases(project_id, requirement_id, testcases)

    def update_testcase(self, project_id, testcase_id, payload):
        return self.testcase_store.update_testcase(project_id, testcase_id, payload)

    def delete_testcase(self, project_id, testcase_id):
        return self.testcase_store.delete_testcase(project_id, testcase_id)

    def delete_testcases_by_requirement(self, project_id, requirement_id):
        return self.testcase_store.delete_testcases_by_requirement(project_id, requirement_id)
