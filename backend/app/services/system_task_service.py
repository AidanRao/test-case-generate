class SystemTaskService:
    MIN_INTERVAL_SECONDS = 5
    MAX_INTERVAL_SECONDS = 86400

    def __init__(self, storage, scheduler=None):
        self.storage = storage
        self.scheduler = scheduler

    def list_tasks(self):
        return self.storage.list_system_tasks(self.scheduler)

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
        task = self.storage.save_system_task(
            task_id,
            update_payload,
            self.scheduler,
        )
        return (task, None) if task else (None, "not_found")

    def run_task(self, task_id):
        task = next(
            (item for item in self.storage.list_system_tasks(self.scheduler) if item.get("id") == task_id),
            None,
        )
        if task is None:
            return None, "not_found"
        if not task.get("available"):
            return None, "unavailable"
        executed = self.storage.run_system_task(task_id, self.scheduler)
        return (executed, None) if executed else (None, "not_found")
