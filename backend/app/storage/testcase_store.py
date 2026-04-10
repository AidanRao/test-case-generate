from app.models.testcase import TestCase


class TestCaseStore:
    def __init__(self, io, path):
        self.io = io
        self.path = path

    def _load_testcases(self):
        raw = self.io.load(self.path, [])
        return [TestCase.from_dict(item) for item in raw]

    def _save_testcases(self, testcases):
        self.io.save(self.path, [item.to_dict() for item in testcases])

    def list_testcases(self, project_id, requirement_id):
        testcases = self._load_testcases()
        return [
            item.to_dict()
            for item in testcases
            if str(item.project_id) == str(project_id)
            and str(item.requirement_id) == str(requirement_id)
        ]

    def list_project_testcases(self, project_id):
        testcases = self._load_testcases()
        return [item.to_dict() for item in testcases if str(item.project_id) == str(project_id)]

    def add_testcases(self, project_id, requirement_id, testcases):
        stored = self._load_testcases()
        for tc in testcases:
            item = TestCase.from_dict(tc)
            item.project_id = project_id
            item.requirement_id = requirement_id
            stored.append(item)
        self._save_testcases(stored)
        return testcases

    def update_testcase(self, project_id, testcase_id, payload):
        testcases = self._load_testcases()
        updated = False
        for idx, item in enumerate(testcases):
            if str(item.project_id) == str(project_id) and str(item.id) == str(testcase_id):
                new_item = item.to_dict()
                new_item.update(payload)
                new_item["id"] = item.id
                new_item["project_id"] = item.project_id
                new_item["requirement_id"] = item.requirement_id
                testcases[idx] = TestCase.from_dict(new_item)
                updated = True
                break
        if updated:
            self._save_testcases(testcases)
        return updated

    def delete_testcase(self, project_id, testcase_id):
        testcases = self._load_testcases()
        filtered = [
            item
            for item in testcases
            if not (str(item.project_id) == str(project_id) and str(item.id) == str(testcase_id))
        ]
        if len(filtered) == len(testcases):
            return False
        self._save_testcases(filtered)
        return True

    def delete_testcases_by_requirement(self, project_id, requirement_id):
        testcases = self._load_testcases()
        filtered = [
            item
            for item in testcases
            if not (
                str(item.project_id) == str(project_id)
                and str(item.requirement_id) == str(requirement_id)
            )
        ]
        if len(filtered) == len(testcases):
            return False
        self._save_testcases(filtered)
        return True

    def delete_by_project(self, project_id):
        testcases = self._load_testcases()
        filtered = [item for item in testcases if str(item.project_id) != str(project_id)]
        self._save_testcases(filtered)
