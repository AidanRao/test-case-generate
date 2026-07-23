class StorageBackend:
    def list_projects(self, keyword=None, portal_project_id=None):
        raise NotImplementedError()

    def get_project_counts(self, project_ids):
        raise NotImplementedError()

    def get_project(self, project_id):
        raise NotImplementedError()

    def create_project(self, payload):
        raise NotImplementedError()

    def update_project(self, project_id, payload):
        raise NotImplementedError()

    def delete_project(self, project_id):
        raise NotImplementedError()

    def list_requirements(self, project_id, module=None, req_type=None, keyword=None):
        raise NotImplementedError()

    def get_requirement(self, project_id, requirement_id):
        raise NotImplementedError()

    def update_requirement(self, project_id, requirement_id, payload):
        raise NotImplementedError()

    def complete_requirements(self, project_id, requirements, scope):
        raise NotImplementedError()

    def list_testcases(self, project_id, requirement_id):
        raise NotImplementedError()

    def list_project_testcases(self, project_id):
        raise NotImplementedError()

    def get_project_quality(self, project_id):
        raise NotImplementedError()

    def save_project_quality(self, project_id, payload):
        raise NotImplementedError()

    def add_testcases(self, project_id, requirement_id, testcases):
        raise NotImplementedError()

    def replace_testcases_by_requirement(self, project_id, requirement_id, testcases):
        raise NotImplementedError()

    def update_testcase(self, project_id, testcase_id, payload):
        raise NotImplementedError()

    def delete_testcase(self, project_id, testcase_id):
        raise NotImplementedError()

    def delete_testcases_by_requirement(self, project_id, requirement_id):
        raise NotImplementedError()

    def get_ai_config(self, config_id):
        raise NotImplementedError()

    def list_ai_configs(self):
        raise NotImplementedError()

    def create_ai_config(self, payload):
        raise NotImplementedError()

    def update_ai_config(self, config_id, payload):
        raise NotImplementedError()

    def delete_ai_config(self, config_id):
        raise NotImplementedError()

    def get_default_ai_config(self):
        raise NotImplementedError()
