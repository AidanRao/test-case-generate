from flask import Blueprint, current_app, request

from app.services.project_service import ProjectService
from app.utils.generation_guard import reject_while_testcases_are_generating
from app.utils.responses import error, ok

projects_bp = Blueprint("projects", __name__)


@projects_bp.get("/projects")
def list_projects():
    service = ProjectService(current_app.config["STORAGE"])
    items = service.list_project_summaries(
        keyword=request.args.get("keyword"),
        portal_project_id=request.args.get("portal_project_id"),
    )
    return ok({"list": items})


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
    service = ProjectService(current_app.config["STORAGE"])
    project = service.get_project_detail(project_id)
    if project is None:
        return error(40401, "资源不存在", 404)
    return ok(project)


@projects_bp.put("/projects/<project_id>")
@reject_while_testcases_are_generating
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


@projects_bp.post("/projects/<project_id>/modules")
@reject_while_testcases_are_generating
def create_module(project_id):
    payload = request.get_json(silent=True) or {}
    storage = current_app.config["STORAGE"]
    if storage.is_read_only_project(project_id):
        return error(40301, "UniPortal 来源项目为只读，请在 UniPortal 中管理", 403)
    service = ProjectService(storage)
    module_name, err = service.create_module(project_id, payload)
    if err == "invalid":
        return error(40001, "模块名不能为空", 400)
    if err == "duplicate":
        return error(40901, "模块名已存在", 409)
    if err == "not_found":
        return error(40401, "资源不存在", 404)
    return ok({"name": module_name})


@projects_bp.delete("/projects/<project_id>")
@reject_while_testcases_are_generating
def delete_project(project_id):
    storage = current_app.config["STORAGE"]
    if storage.is_read_only_project(project_id):
        return error(40301, "UniPortal 来源项目为只读，请在 UniPortal 中管理", 403)
    service = ProjectService(storage)
    deleted = service.delete_project(project_id)
    if not deleted:
        return error(40401, "资源不存在", 404)
    return ok({"deleted": True})
