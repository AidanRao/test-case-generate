from flask import Blueprint, current_app, request

from app.services.ai_config_service import AIConfigService
from app.utils.responses import error, ok

ai_config_bp = Blueprint("ai_config", __name__)


@ai_config_bp.get("/ai/configs")
def list_configs():
    storage = current_app.config["STORAGE"]
    service = AIConfigService(storage)
    configs = service.list_configs()
    return ok({"list": configs})


@ai_config_bp.get("/ai/configs/<config_id>")
def get_config(config_id):
    storage = current_app.config["STORAGE"]
    service = AIConfigService(storage)
    config = service.get_config(config_id)
    if not config:
        return error(40401, "资源不存在", 404)
    return ok(config)


@ai_config_bp.post("/ai/configs")
def create_config():
    payload = request.get_json(silent=True) or {}
    if not payload.get("api_key"):
        return error(40001, "api_key 必填", 400)
    storage = current_app.config["STORAGE"]
    service = AIConfigService(storage)
    config = service.create_config(payload)
    if not config:
        return error(50001, "创建失败", 500)
    return ok(config)


@ai_config_bp.put("/ai/configs/<config_id>")
def update_config(config_id):
    payload = request.get_json(silent=True) or {}
    storage = current_app.config["STORAGE"]
    service = AIConfigService(storage)
    config = service.update_config(config_id, payload)
    if not config:
        return error(40401, "资源不存在", 404)
    return ok(config)


@ai_config_bp.delete("/ai/configs/<config_id>")
def delete_config(config_id):
    storage = current_app.config["STORAGE"]
    service = AIConfigService(storage)
    deleted = service.delete_config(config_id)
    if not deleted:
        return error(40401, "资源不存在", 404)
    return ok({"deleted": True})


@ai_config_bp.get("/ai/configs/default")
def get_default_config():
    storage = current_app.config["STORAGE"]
    service = AIConfigService(storage)
    config = service.get_default_config()
    return ok(config or {})