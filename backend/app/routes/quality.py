from flask import Blueprint, current_app

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
