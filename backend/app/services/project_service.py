class ProjectService:
    def __init__(self, storage):
        self.storage = storage

    def list_projects(self, keyword=None, portal_project_id=None):
        return self.storage.list_projects(keyword, portal_project_id)

    def get_project_counts(self, project_ids):
        return self.storage.get_project_counts(project_ids)

    def get_project(self, project_id):
        return self.storage.get_project(project_id)

    def create_project(self, payload):
        code = payload.get("code", "")
        if self._code_exists(code):
            return None, "duplicate"
        project_id = self.storage.create_project(payload)
        requirements = payload.get("requirements", [])
        print(requirements)
        if requirements:
            self.storage.complete_requirements(project_id, requirements, "project")
        return project_id, None

    def update_project(self, project_id, payload):
        code = payload.get("code")
        if code and self._code_exists(code, exclude_project_id=project_id):
            return False, "duplicate"
        updated = self.storage.update_project(project_id, payload)
        return updated, None if updated else "not_found"

    def delete_project(self, project_id):
        return self.storage.delete_project(project_id)

    def _code_exists(self, code, exclude_project_id=None):
        if not code:
            return False
        if hasattr(self.storage, "project_code_exists"):
            return self.storage.project_code_exists(code, exclude_project_id)
        projects = self.storage.list_projects()
        for project in projects:
            if exclude_project_id is not None and str(project.get("id")) == str(
                exclude_project_id
            ):
                continue
            if project.get("code") == code:
                return True
        return False
