from flask import Blueprint, current_app, request

from app.services.requirement_service import RequirementService
from app.utils.generation_guard import reject_while_testcases_are_generating
from app.utils.responses import error, ok

requirements_bp = Blueprint("requirements", __name__)


@requirements_bp.get("/projects/<project_id>/requirements")
def list_requirements(project_id):
    module = request.args.get("module")
    req_type = request.args.get("type")
    keyword = request.args.get("keyword")
    storage = current_app.config["STORAGE"]
    service = RequirementService(storage)
    items = service.list_requirements(project_id, module, req_type, keyword)
    if items is None:
        return error(40401, "资源不存在", 404)
    return ok({"list": items})


@requirements_bp.get("/projects/<project_id>/requirements/<requirement_id>")
def get_requirement(project_id, requirement_id):
    storage = current_app.config["STORAGE"]
    service = RequirementService(storage)
    item = service.get_requirement(project_id, requirement_id)
    if not item:
        return error(40401, "资源不存在", 404)
    return ok(item)


@requirements_bp.put("/projects/<project_id>/requirements/<requirement_id>")
@reject_while_testcases_are_generating
def update_requirement(project_id, requirement_id):
    payload = request.get_json(silent=True) or {}
    storage = current_app.config["STORAGE"]
    if storage.is_read_only_project(project_id):
        return error(40301, "UniPortal 来源需求为只读，请在 UniPortal 中管理", 403)
    service = RequirementService(storage)
    updated = service.update_requirement(project_id, requirement_id, payload)
    if not updated:
        return error(40401, "资源不存在", 404)
    return ok({"updated": True})


@requirements_bp.post("/projects/<project_id>/requirements/complete")
@reject_while_testcases_are_generating
def complete_requirements(project_id):
    payload = request.get_json(silent=True) or {}
    requirements = payload.get("requirements", [])
    scope = payload.get("scope", "project")
    storage = current_app.config["STORAGE"]
    if storage.is_read_only_project(project_id):
        return error(40301, "UniPortal 来源需求为只读，请在 UniPortal 中管理", 403)
    service = RequirementService(storage)
    result = service.complete_requirements(project_id, requirements, scope)
    if result is None:
        return error(40401, "资源不存在", 404)
    return ok(result)


@requirements_bp.post("/projects/<project_id>/requirements")
@reject_while_testcases_are_generating
def create_requirement(project_id):
    payload = request.get_json(silent=True) or {}
    storage = current_app.config["STORAGE"]
    if storage.is_read_only_project(project_id):
        return error(40301, "UniPortal 来源需求为只读，请在 UniPortal 中管理", 403)
    service = RequirementService(storage)
    new_req = service.create_requirement(project_id, payload)
    if new_req is None:
        return error(40401, "资源不存在", 404)
    return ok(new_req)


@requirements_bp.delete("/projects/<project_id>/requirements/<requirement_id>")
@reject_while_testcases_are_generating
def delete_requirement(project_id, requirement_id):
    storage = current_app.config["STORAGE"]
    if storage.is_read_only_project(project_id):
        return error(40301, "UniPortal 来源需求为只读，请在 UniPortal 中管理", 403)
    service = RequirementService(storage)
    deleted = service.delete_requirement(project_id, requirement_id)
    if deleted is None:
        return error(40401, "资源不存在", 404)
    if not deleted:
        return error(40401, "资源不存在", 404)
    return ok({"deleted": True})
