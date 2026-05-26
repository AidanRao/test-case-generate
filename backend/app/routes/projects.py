from flask import Blueprint, current_app, request

from app.services.project_service import ProjectService
from app.utils.responses import error, ok

projects_bp = Blueprint("projects", __name__)


@projects_bp.get("/projects")
def list_projects():
    storage = current_app.config["STORAGE"]
    service = ProjectService(storage)
    projects = service.list_projects(
        keyword=request.args.get("keyword"),
        portal_project_id=request.args.get("portal_project_id"),
    )
    project_ids = [project.get("id") for project in projects]
    counts = service.get_project_counts(project_ids)
    data = {
        "list": [
            {
                "id": p.get("id"),
                "code": p.get("code"),
                "title": p.get("title"),
                "source": p.get("source", "local"),
                "module_count": counts.get(str(p.get("id")), {}).get("module_count", 0),
                "requirement_count": counts.get(str(p.get("id")), {}).get(
                    "requirement_count", 0
                ),
            }
            for p in projects
        ]
    }
    return ok(data)


@projects_bp.post("/projects")
def create_project():
    payload = request.get_json(silent=True) or {}
    storage = current_app.config["STORAGE"]
    service = ProjectService(storage)
    project_id, err = service.create_project(payload)
    if err == "duplicate":
        return error(40901, "项目编号重复", 409)
    return ok({"id": project_id})


@projects_bp.get("/projects/<project_id>")
def get_project(project_id):
    storage = current_app.config["STORAGE"]
    service = ProjectService(storage)
    project = service.get_project(project_id)
    if not project:
        return error(40401, "资源不存在", 404)
    requirements = storage.list_requirements(project_id) or []
    testcases = storage.list_project_testcases(project_id) or []
    testcase_map = {}
    for testcase in testcases:
        requirement_id = str(testcase.get("requirement_id", ""))
        testcase_map.setdefault(requirement_id, []).append(testcase)
    for requirement in requirements:
        requirement_id = str(requirement.get("id", ""))
        requirement["testcases"] = testcase_map.get(requirement_id, [])
    project["requirements"] = requirements
    return ok(project)


@projects_bp.put("/projects/<project_id>")
def update_project(project_id):
    payload = request.get_json(silent=True) or {}
    storage = current_app.config["STORAGE"]
    if storage.is_read_only_project(project_id):
        return error(40301, "UniPortal 来源项目为只读，请在 UniPortal 中管理", 403)
    service = ProjectService(storage)
    updated, err = service.update_project(project_id, payload)
    if err == "duplicate":
        return error(40901, "项目编号重复", 409)
    if not updated:
        return error(40401, "资源不存在", 404)
    return ok({"updated": True})


@projects_bp.delete("/projects/<project_id>")
def delete_project(project_id):
    storage = current_app.config["STORAGE"]
    if storage.is_read_only_project(project_id):
        return error(40301, "UniPortal 来源项目为只读，请在 UniPortal 中管理", 403)
    service = ProjectService(storage)
    deleted = service.delete_project(project_id)
    if not deleted:
        return error(40401, "资源不存在", 404)
    return ok({"deleted": True})
