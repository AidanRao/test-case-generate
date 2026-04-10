from app.models.project import Project
from app.utils.ids import new_uuid


class ProjectStore:
    def __init__(self, io, path):
        self.io = io
        self.path = path

    def _load_projects(self):
        raw = self.io.load(self.path, [])
        return [Project.from_dict(item) for item in raw]

    def _save_projects(self, projects):
        self.io.save(self.path, [project.to_dict() for project in projects])

    def list_projects(self, keyword=None):
        projects = self._load_projects()
        if not keyword:
            return [project.to_dict() for project in projects]
        keyword_lower = keyword.lower()
        return [
            project.to_dict()
            for project in projects
            if keyword_lower in project.title.lower() or keyword_lower in project.code.lower()
        ]

    def get_project(self, project_id):
        projects = self._load_projects()
        for project in projects:
            if str(project.id) == str(project_id):
                return project
        return None

    def save_project(self, project):
        projects = self._load_projects()
        for idx, item in enumerate(projects):
            if str(item.id) == str(project.id):
                projects[idx] = project
                self._save_projects(projects)
                return True
        return False

    def create_project(self, payload):
        projects = self._load_projects()
        project_id = new_uuid()
        project = Project(
            id=project_id,
            code=payload.get("code", ""),
            title=payload.get("title", ""),
        )
        projects.append(project)
        self._save_projects(projects)
        return project_id

    def update_project(self, project_id, payload):
        projects = self._load_projects()
        updated = False
        for idx, project in enumerate(projects):
            if str(project.id) == str(project_id):
                new_project = Project(
                    id=project.id,
                    code=payload.get("code", project.code),
                    title=payload.get("title", project.title),
                )
                projects[idx] = new_project
                updated = True
                break
        if updated:
            self._save_projects(projects)
        return updated

    def delete_project(self, project_id):
        projects = self._load_projects()
        filtered = [project for project in projects if str(project.id) != str(project_id)]
        if len(filtered) == len(projects):
            return False
        self._save_projects(filtered)
        return True
