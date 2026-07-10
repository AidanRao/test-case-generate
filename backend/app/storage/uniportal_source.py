import json
import os

from app.models.requirement import Requirement


PROJECT_NAME_EXCLUDED_DIRECTORIES = {
    "configuration-test-case-generate",
    "document-validator",
}


class DocumentValidatorRequirementAdapter:
    def normalize(self, project_id, payload):
        if not isinstance(payload, list):
            return []
        nodes_by_id = {
            str(item.get("id")): item
            for item in payload
            if isinstance(item, dict) and item.get("id") is not None
        }
        normalized = []
        for item in payload:
            if not isinstance(item, dict) or not self._is_requirement(
                item.get("is_req")
            ):
                continue
            content = self._build_content(item.get("content"), item.get("tables"))
            requirement_data = {
                "id": str(item.get("id", "")),
                "title": item.get("title", ""),
                "type": item.get("type", ""),
                "code": str(item.get("id", "")),
                "content": content,
            }
            requirement = Requirement.from_dict(
                requirement_data,
                module=self._find_module(item, nodes_by_id),
                project_id=project_id,
            )
            normalized.append(requirement.to_dict())
        return normalized

    def _is_requirement(self, value):
        return value not in (0, "0", None, False)

    def _find_module(self, item, nodes_by_id):
        parent = nodes_by_id.get(str(item.get("parent_id")))
        return parent.get("title", "") if parent else ""

    def _build_content(self, content, tables):
        parts = []
        if content:
            parts.append(str(content))
        if isinstance(tables, list):
            for table in tables:
                rendered = self._render_table(table)
                if rendered:
                    parts.append(rendered)
        return "\n\n".join(parts)

    def _render_table(self, table):
        if not isinstance(table, dict):
            return json.dumps(table, ensure_ascii=False)
        lines = []
        caption = table.get("caption") or table.get("id")
        if caption:
            lines.append(f"表格：{caption}")
        headers = table.get("headers")
        if isinstance(headers, list) and headers:
            lines.append(self._render_markdown_table_row(headers))
            lines.append(self._render_markdown_table_row(["---"] * len(headers)))
        rows = table.get("rows")
        if isinstance(rows, list):
            for row in rows:
                if isinstance(row, list):
                    lines.append(self._render_markdown_table_row(row))
                else:
                    lines.append(str(row))
        return "\n".join(lines)

    def _render_markdown_table_row(self, row):
        return "| " + " | ".join(self._render_markdown_table_cell(item) for item in row) + " |"

    def _render_markdown_table_cell(self, value):
        return str(value).replace("|", "\\|").replace("\n", "<br>")


class UniPortalRequirementSource:
    """Read-only view over Document Validator requirement files uploaded through UniPortal."""

    def __init__(self, storage_path):
        self.storage_path = os.path.abspath(storage_path) if storage_path else None
        self.document_validator_adapter = DocumentValidatorRequirementAdapter()

    @property
    def enabled(self):
        return bool(self.storage_path and os.path.isdir(self.storage_path))

    def _iter_items(self):
        if not self.enabled:
            return
        for current_project_id in sorted(os.listdir(self.storage_path)):
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
        source_roots = [
            name for name in source_roots if name not in PROJECT_NAME_EXCLUDED_DIRECTORIES
        ]
        return source_roots[0] if source_roots else None

    def _find_requirement_file(self, item_path, requirement_path):
        path = os.path.join(item_path, requirement_path)
        return path if os.path.isfile(path) else None

    def _normalize_requirements(self, project_id, file_path):
        try:
            with open(file_path, "r", encoding="utf-8") as source:
                payload = json.load(source)
        except (OSError, json.JSONDecodeError):
            return []

        return self.document_validator_adapter.normalize(project_id, payload)

    def _build_project(self, portal_project_id, item_id, item_path):
        project_code = item_id
        project_name = self._project_name(item_id, item_path)
        if not project_name:
            return None
        return {
            "code": project_code,
            "title": project_name,
            "portal_project_id": portal_project_id,
        }

    def discover_projects(self, requirement_path):
        projects = []
        for current_project_id, item_id, item_path in self._iter_items() or []:
            if not self._find_requirement_file(item_path, requirement_path):
                continue
            project = self._build_project(current_project_id, item_id, item_path)
            if project:
                projects.append(project)
        return projects

    def list_requirements(
        self, project_code, requirement_path, module=None, req_type=None, keyword=None
    ):
        item_path = None
        for _, item_id, path in self._iter_items() or []:
            if str(item_id) == str(project_code):
                item_path = path
                break
        if item_path is None:
            return None

        file_path = self._find_requirement_file(item_path, requirement_path)
        if not file_path:
            return None
        items = self._normalize_requirements(str(project_code), file_path)
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
