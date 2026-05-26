import json
import os
import uuid

from app.models.requirement import Requirement


class UniPortalRequirementSource:
    """Read-only view over requirements.json files uploaded through UniPortal."""

    def __init__(self, storage_path):
        self.storage_path = os.path.abspath(storage_path) if storage_path else None

    @property
    def enabled(self):
        return bool(self.storage_path and os.path.isdir(self.storage_path))

    def _iter_items(self, portal_project_id=None):
        if not self.enabled:
            return
        for current_project_id in sorted(os.listdir(self.storage_path)):
            if portal_project_id and current_project_id != portal_project_id:
                continue
            portal_path = os.path.join(self.storage_path, current_project_id)
            if current_project_id.startswith(".") or not os.path.isdir(portal_path):
                continue
            for item_id in sorted(os.listdir(portal_path)):
                item_path = os.path.join(portal_path, item_id)
                if item_id.startswith((".", "_")) or not os.path.isdir(item_path):
                    continue
                yield current_project_id, item_id, item_path

    def _visible_directories(self, item_path):
        try:
            return sorted(
                name
                for name in os.listdir(item_path)
                if not name.startswith((".", "_"))
                and os.path.isdir(os.path.join(item_path, name))
            )
        except OSError:
            return []

    def _project_name(self, item_id, item_path):
        source_roots = self._visible_directories(item_path)
        return source_roots[0] if source_roots else item_id

    def _find_requirement_files(self, item_path):
        source_roots = self._visible_directories(item_path)
        candidates = [
            os.path.join(item_path, source_roots[0], "requirements.json")
        ] if source_roots else []
        # Keep reading the former flat layout while existing shared data is migrated.
        candidates.append(os.path.join(item_path, "requirements.json"))
        return [path for path in candidates if os.path.isfile(path)][:1]

    def _normalize_requirements(self, project_id, item_path, file_path):
        try:
            with open(file_path, "r", encoding="utf-8") as source:
                payload = json.load(source)
        except (OSError, json.JSONDecodeError):
            return []

        if isinstance(payload, dict):
            groups = [payload]
        elif isinstance(payload, list):
            groups = payload
        else:
            return []

        normalized = []
        default_module = os.path.basename(os.path.dirname(file_path))
        for group_index, group in enumerate(groups):
            if not isinstance(group, dict):
                continue
            if isinstance(group.get("requirements"), list):
                module = group.get("module", "")
                requirements = group["requirements"]
            else:
                module = group.get("module", default_module)
                requirements = [group]
            for requirement_index, item in enumerate(requirements):
                if not isinstance(item, dict):
                    continue
                requirement = Requirement.from_dict(
                    item, module=module, project_id=project_id
                )
                if not requirement.id:
                    relative_path = os.path.relpath(file_path, item_path)
                    key = (
                        f"uniportal:{project_id}:{relative_path}:"
                        f"{group_index}:{requirement_index}:{requirement.code}"
                    )
                    requirement.id = str(uuid.uuid5(uuid.NAMESPACE_URL, key))
                normalized.append(requirement.to_dict())
        return normalized

    def _build_project(self, portal_project_id, item_id, item_path):
        project_code = item_id
        project_name = self._project_name(item_id, item_path)
        return {
            "code": project_code,
            "title": project_name,
            "portal_project_id": portal_project_id,
        }

    def discover_projects(self, portal_project_id=None):
        projects = []
        for current_project_id, item_id, item_path in self._iter_items(portal_project_id) or []:
            if not self._find_requirement_files(item_path):
                continue
            projects.append(self._build_project(current_project_id, item_id, item_path))
        return projects

    def list_requirements(self, project_code, module=None, req_type=None, keyword=None):
        item_path = None
        for _, item_id, path in self._iter_items() or []:
            if str(item_id) == str(project_code):
                item_path = path
                break
        if item_path is None or not self._find_requirement_files(item_path):
            return None

        items = []
        for file_path in self._find_requirement_files(item_path):
            items.extend(
                self._normalize_requirements(str(project_code), item_path, file_path)
            )
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
