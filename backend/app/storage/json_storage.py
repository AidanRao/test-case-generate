import os

from app.storage.base import StorageBackend
from app.storage.json_io import JsonIO
from app.storage.project_store import ProjectStore
from app.storage.requirement_store import RequirementStore
from app.storage.testcase_store import TestCaseStore
from app.storage.ai_config_store import AIConfigStore


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
        self.ai_config_store = AIConfigStore(io, os.path.join(self.data_dir, "ai_configs.json"))

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

    def get_ai_config(self, config_id):
        config = self.ai_config_store.get_config(config_id)
        return config.to_dict() if config else None

    def list_ai_configs(self):
        configs = self.ai_config_store.list_configs()
        return [config.to_dict() for config in configs]

    def create_ai_config(self, payload):
        config = self.ai_config_store.create_config(payload)
        return config.to_dict() if config else None

    def update_ai_config(self, config_id, payload):
        config = self.ai_config_store.update_config(config_id, payload)
        return config.to_dict() if config else None

    def delete_ai_config(self, config_id):
        return self.ai_config_store.delete_config(config_id)

    def get_default_ai_config(self):
        config = self.ai_config_store.get_default_config()
        return config.to_dict() if config else None
