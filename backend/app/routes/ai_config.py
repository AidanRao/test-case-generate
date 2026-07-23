from flask import Blueprint, current_app, request

from app.services.ai_config_service import AIConfigService
from app.utils.responses import error, ok

ai_config_bp = Blueprint("ai_config", __name__)


@ai_config_bp.get("/ai/config")
def get_config():
    storage = current_app.config["STORAGE"]
    service = AIConfigService(storage)
    config = service.get_config()
    return ok(config or {})


@ai_config_bp.put("/ai/config")
def save_config():
    payload = request.get_json(silent=True) or {}
    storage = current_app.config["STORAGE"]
    service = AIConfigService(storage)
    config = service.save_config(payload)
    if not config:
        return error(50001, "保存失败", 500)
    return ok(config)


@ai_config_bp.post("/ai/config/test")
def test_connection():
    payload = request.get_json(silent=True) or {}
    storage = current_app.config["STORAGE"]
    service = AIConfigService(storage)
    return ok(service.test_connection(payload))
