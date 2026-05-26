from flask import Blueprint, current_app, request

from app.services.system_task_service import SystemTaskService
from app.utils.responses import error, ok

system_tasks_bp = Blueprint("system_tasks", __name__)


@system_tasks_bp.get("/system/tasks")
def list_system_tasks():
    service = SystemTaskService(current_app.config["STORAGE"])
    return ok({"list": service.list_tasks()})


@system_tasks_bp.put("/system/tasks/<task_id>")
def update_system_task(task_id):
    payload = request.get_json(silent=True) or {}
    service = SystemTaskService(current_app.config["STORAGE"])
    task, err = service.update_task(task_id, payload)
    if err == "not_found":
        return error(40401, "定时任务不存在", 404)
    if err:
        return error(40001, "启用状态或执行间隔不合法", 400)
    return ok(task)
