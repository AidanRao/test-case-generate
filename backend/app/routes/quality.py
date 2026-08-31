from flask import Blueprint, current_app

from app.services.coverage_service import CoverageService
from app.services.quality_service import QualityService
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
def calculate_coverage(project_id):
    job = current_app.extensions["coverage_job_manager"].submit(project_id)
    response = ok(job)
    response.status_code = 202
    return response


@quality_bp.get("/projects/<project_id>/coverage/calculation-jobs")
def get_project_coverage_calculation_status(project_id):
    manager = current_app.extensions["coverage_job_manager"]
    return ok(manager.get_project_status(project_id))


@quality_bp.get("/projects/<project_id>/coverage/calculation-jobs/<job_id>")
def get_coverage_calculation_job(project_id, job_id):
    manager = current_app.extensions["coverage_job_manager"]
    return ok(manager.get_project_job(project_id, job_id))
