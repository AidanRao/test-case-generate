from copy import deepcopy


class SystemTaskStore:
    def __init__(self, io, file_path):
        self.io = io
        self.file_path = file_path

    def list_tasks(self):
        tasks = self.io.load(self.file_path, [])
        return [
            deepcopy(item)
            for item in tasks
            if isinstance(item, dict) and item.get("id")
        ]

    def sync_registered_tasks(self, registered_tasks, overrides=None):
        overrides = overrides or {}
        tasks = self.list_tasks()
        known_ids = {item["id"] for item in tasks}
        changed = False
        for registered_task in registered_tasks:
            if registered_task.id in known_ids:
                continue
            tasks.append(
                registered_task.to_store_record(overrides.get(registered_task.id))
            )
            known_ids.add(registered_task.id)
            changed = True
        if changed:
            self.io.save(self.file_path, tasks)

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
                "interval_seconds": int(
                    payload.get("interval_seconds", task.get("interval_seconds", 30))
                ),
            }
            tasks[index] = updated
            self.io.save(self.file_path, tasks)
            return deepcopy(updated)
        return None