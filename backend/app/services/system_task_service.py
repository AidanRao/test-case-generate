class SystemTaskService:
    MIN_INTERVAL_SECONDS = 5
    MAX_INTERVAL_SECONDS = 86400

    def __init__(self, task_manager):
        self.task_manager = task_manager

    def list_tasks(self):
        return self.task_manager.list_tasks()

    def update_task(self, task_id, payload):
        enabled = payload.get("enabled")
        interval_seconds = payload.get("interval_seconds")
        if not isinstance(enabled, bool):
            return None, "invalid_enabled"
        if isinstance(interval_seconds, bool):
            return None, "invalid_interval"
        try:
            interval_seconds = int(interval_seconds)
        except (TypeError, ValueError):
            return None, "invalid_interval"
        if not self.MIN_INTERVAL_SECONDS <= interval_seconds <= self.MAX_INTERVAL_SECONDS:
            return None, "invalid_interval"
        kwargs = payload.get("kwargs", {})
        if not isinstance(kwargs, dict):
            return None, "invalid_kwargs"
        update_payload = {
            "enabled": enabled,
            "interval_seconds": interval_seconds,
            "kwargs": kwargs,
        }
        task = self.task_manager.update_task(task_id, update_payload)
        return (task, None) if task else (None, "not_found")

    def run_task(self, task_id):
        task = self.task_manager.get_task(task_id)
        if task is None:
            return None, "not_found"
        if not task.get("available"):
            return None, "unavailable"
        executed = self.task_manager.run_task(task_id)
        return (executed, None) if executed else (None, "not_found")
