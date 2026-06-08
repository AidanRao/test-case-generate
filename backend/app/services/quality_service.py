class QualityService:
    def __init__(self, storage):
        self.storage = storage

    def get_quality(self, project_id):
        project = self.storage.get_project(project_id)
        if not project:
            return None
        saved_quality = self.storage.get_project_quality(project_id)
        if saved_quality:
            return saved_quality
        testcases = self.storage.list_project_testcases(project_id)
        success_count = len(testcases)
        iterations = 1 if success_count > 0 else 0
        return {
            "success_count": success_count,
            "fail_count": 0,
            "iterations": iterations,
            "duration": 0,
        }
