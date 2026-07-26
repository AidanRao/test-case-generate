from flask import Blueprint, current_app

from app.services.quality_service import QualityService
from app.services.coverage_service import CoverageService
from app.utils.generation_guard import reject_while_testcases_are_generating
from app.utils.responses import error, ok

quality_bp = Blueprint("quality", __name__)


@quality_bp.get("/projects/<project_id>/quality")
def get_quality(project_id):
    storage = current_app.config["STORAGE"]
    service = QualityService(storage)
    data = service.get_quality(project_id)
    if data is None:
        return error(40401, "资源不存在", 404)
    return ok(data)


@quality_bp.get("/projects/<project_id>/coverage")
def get_coverage(project_id):
    storage = current_app.config["STORAGE"]
    config = current_app.config["APP_CONFIG"]
    data, err = CoverageService(storage, config).get_coverage(project_id)
    if err == "not_found":
        return error(40401, "资源不存在", 404)
    return ok(data)


@quality_bp.post("/projects/<project_id>/coverage/calculate")
@reject_while_testcases_are_generating
def calculate_coverage(project_id):
    storage = current_app.config["STORAGE"]
    if not storage.get_project(project_id):
        return error(40401, "资源不存在", 404)
    requirements = storage.list_requirements(project_id) or []
    if not requirements:
        return error(40001, "项目暂无需求，无法计算覆盖率", 400)

    manager = current_app.extensions["coverage_job_manager"]
    job, active_job = manager.submit(project_id, requirements)
    if active_job:
        return error(
            40903,
            "该项目已有覆盖率计算任务正在进行",
            409,
            active_job,
        )
    response = ok(job)
    response.status_code = 202
    return response


@quality_bp.get("/projects/<project_id>/coverage/calculation-jobs")
def get_project_coverage_calculation_status(project_id):
    storage = current_app.config["STORAGE"]
    if not storage.get_project(project_id):
        return error(40401, "资源不存在", 404)
    manager = current_app.extensions["coverage_job_manager"]
    return ok(manager.get_project_status(project_id))


@quality_bp.get("/projects/<project_id>/coverage/calculation-jobs/<job_id>")
def get_coverage_calculation_job(project_id, job_id):
    manager = current_app.extensions["coverage_job_manager"]
    job = manager.get_job(job_id)
    if not job or str(job["project_id"]) != str(project_id):
        return error(40401, "资源不存在", 404)
    return ok(job)
