class QualityService:
    def __init__(self, storage):
        self.storage = storage

    def get_quality(self, project_id):
        project = self.storage.get_project(project_id)
        if not project:
            return None
        requirements = self.storage.list_requirements(project_id) or []
        testcases = self.storage.list_project_testcases(project_id)
        req_type_stats = {}
        for req in requirements:
            req_type = req.get("type", "未知类型")
            req_type_stats[req_type] = req_type_stats.get(req_type, 0) + 1
        success_count = len(testcases)
        iterations = 1 if success_count > 0 else 0
        return {
            "success_count": success_count,
            "fail_count": 0,
            "iterations": iterations,
            "duration": "0s",
            "req_type_stats": req_type_stats,
        }
