from app.models.requirement import Requirement
from app.utils.ids import new_uuid


def _normalize_project_id(project_id):
    return str(project_id)


class RequirementStore:
    def __init__(self, io, path, project_store):
        self.io = io
        self.path = path
        self.project_store = project_store

    def _load_requirements(self):
        return self.io.load(self.path, [])

    def _save_requirements(self, requirements):
        self.io.save(self.path, requirements)

    def list_requirements(self, project_id, module=None, req_type=None, keyword=None):
        project = self.project_store.get_project(project_id)
        if not project:
            return None
        items = [
            item
            for item in self._load_requirements()
            if str(item.get("project_id")) == str(project_id)
        ]
        if module:
            items = [item for item in items if item.get("module") == module]
        if req_type:
            items = [item for item in items if item.get("type") == req_type]
        if keyword:
            keyword_lower = keyword.lower()
            items = [
                item
                for item in items
                if keyword_lower in str(item.get("title", "")).lower()
                or keyword_lower in str(item.get("content", "")).lower()
            ]
        return items

    def get_requirement(self, project_id, requirement_id):
        project = self.project_store.get_project(project_id)
        if not project:
            return None
        for item in self._load_requirements():
            if str(item.get("project_id")) != str(project_id):
                continue
            if str(item.get("id")) == str(requirement_id):
                return item
        return None

    def update_requirement(self, project_id, requirement_id, payload):
        project = self.project_store.get_project(project_id)
        if not project:
            return False
        stored = self._load_requirements()
        updated = False
        for idx, item in enumerate(stored):
            if str(item.get("project_id")) != str(project_id):
                continue
            if str(item.get("id")) != str(requirement_id):
                continue
            new_item = dict(item)
            for key in ["title", "type", "code", "content", "module"]:
                if key in payload:
                    new_item[key] = payload.get(key)
            stored[idx] = new_item
            updated = True
            break
        if updated:
            self._save_requirements(stored)
        return updated

    def create_requirement(self, project_id, payload):
        project = self.project_store.get_project(project_id)
        if not project:
            return None
        project_id_value = _normalize_project_id(project_id)
        stored = self._load_requirements()
        new_req = Requirement.from_dict(
            payload, module=payload.get("module"), project_id=project_id_value
        )
        new_req.id = new_uuid()
        if not new_req.code:
            new_req.code = f"REQ-{new_req.id.split('-')[0]}"
        stored.append(new_req.to_dict())
        self._save_requirements(stored)
        return new_req.to_dict()

    def complete_requirements(self, project_id, requirements, scope):
        project = self.project_store.get_project(project_id)
        if not project:
            return None
        project_id_value = _normalize_project_id(project_id)
        stored = self._load_requirements()
        project_items = [
            item for item in stored if str(item.get("project_id")) == str(project_id)
        ]
        existing_modules = {
            item.get("module") for item in project_items if item.get("module")
        }
        added_count = 0
        module_added = []
        for group in requirements:
            module = group.get("module")
            if not module:
                continue
            group_added = False
            for req in group.get("requirements", []):
                new_req = Requirement.from_dict(
                    req, module=module, project_id=project_id_value
                )
                new_req.id = new_uuid()
                if not new_req.code:
                    new_req.code = f"REQ-{new_req.id.split('-')[0]}"
                stored.append(new_req.to_dict())
                added_count += 1
                group_added = True
            if group_added and module not in existing_modules:
                module_added.append(module)
                existing_modules.add(module)
        self._save_requirements(stored)
        return {
            "completedRequirements": requirements,
            "diff": {"addedCount": added_count, "moduleAdded": module_added},
        }

    def delete_requirement(self, project_id, requirement_id, testcase_store):
        project = self.project_store.get_project(project_id)
        if not project:
            return None
        stored = self._load_requirements()
        filtered = [
            item
            for item in stored
            if not (str(item.get("project_id")) == str(project_id) and str(item.get("id")) == str(requirement_id))
        ]
        if len(filtered) == len(stored):
            return False
        # Delete associated test cases
        testcase_store.delete_testcases_by_requirement(project_id, requirement_id)
        self._save_requirements(filtered)
        return True

    def delete_by_project(self, project_id):
        stored = self._load_requirements()
        filtered = [item for item in stored if str(item.get("project_id")) != str(project_id)]
        if len(filtered) == len(stored):
            return False
        self._save_requirements(filtered)
        return True

    def get_project_counts(self, project_ids):
        counts = {str(project_id): {"module_count": 0, "requirement_count": 0} for project_id in project_ids}
        module_map = {str(project_id): set() for project_id in project_ids}
        for item in self._load_requirements():
            project_id = str(item.get("project_id"))
            if project_id not in counts:
                continue
            counts[project_id]["requirement_count"] += 1
            module = item.get("module")
            if module:
                module_map[project_id].add(module)
        for project_id, modules in module_map.items():
            counts[project_id]["module_count"] = len(modules)
        return counts
