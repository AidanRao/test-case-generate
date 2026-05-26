import os
from copy import deepcopy


class SystemTaskStore:
    def __init__(self, io, file_path, defaults):
        self.io = io
        self.file_path = file_path
        self.defaults = deepcopy(defaults)
        self._ensure_defaults()

    def _ensure_defaults(self):
        state = self.io.load(self.file_path, {"tasks": []})
        tasks = state.get("tasks", []) if isinstance(state, dict) else []
        normalized = [item for item in tasks if isinstance(item, dict) and item.get("id")]
        known_ids = {item["id"] for item in normalized}
        for default in self.defaults:
            if default["id"] not in known_ids:
                normalized.append(deepcopy(default))
        if normalized != tasks or not os.path.exists(self.file_path):
            self.io.save(self.file_path, {"tasks": normalized})

    def list_tasks(self):
        self._ensure_defaults()
        state = self.io.load(self.file_path, {"tasks": []})
        return [
            deepcopy(item)
            for item in state.get("tasks", [])
            if isinstance(item, dict) and item.get("id")
        ]

    def get_task(self, task_id):
        for task in self.list_tasks():
            if task.get("id") == task_id:
                return task
        return None

    def save_task(self, task_id, payload):
        tasks = self.list_tasks()
        for index, task in enumerate(tasks):
            if task.get("id") != task_id:
                continue
            updated = {
                **task,
                "enabled": bool(payload.get("enabled")),
                "interval_seconds": int(payload.get("interval_seconds")),
            }
            tasks[index] = updated
            self.io.save(self.file_path, {"tasks": tasks})
            return deepcopy(updated)
        return None
