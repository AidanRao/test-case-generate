class ReportQueryService:
    """Load all source records needed to build a project test report."""

    def __init__(self, storage):
        self.storage = storage

    def load(self, project_id):
        project = self.storage.get_project(project_id)
        if not project:
            return None
        return {
            "project": project,
            "requirements": self.storage.list_requirements(project_id) or [],
            "testcases": self.storage.list_project_testcases(project_id) or [],
        }

