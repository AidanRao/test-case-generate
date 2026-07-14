from apscheduler.jobstores.base import ConflictingIdError
from apscheduler.schedulers.background import BackgroundScheduler

from app.task_registry import TASK_REGISTRY


class SystemTaskManager:
    """Owns registered task configuration, persistence, execution and scheduling."""

    def __init__(self, task_store, context, scheduler=None):
        import app.tasks  # noqa: F401

        self.task_store = task_store
        self.context = context
        self.scheduler = scheduler or BackgroundScheduler(timezone="Asia/Shanghai")

    def start(self):
        self._sync_registered_tasks()
        self._load_jobs()
        if not self.scheduler.running:
            self.scheduler.start()

    def shutdown(self, wait=True):
        if self.scheduler.running:
            self.scheduler.shutdown(wait=wait)

    def list_tasks(self):
        return [self._with_runtime(task) for task in self.task_store.list_tasks()]

    def get_task(self, task_id):
        task = self.task_store.get_task(task_id)
        return self._with_runtime(task) if task else None

    def update_task(self, task_id, payload):
        task = self.task_store.save_task(task_id, payload)
        if task is None:
            return None
        self._update_job(task)
        return self._with_runtime(task)

    def run_task(self, task_id):
        stored_task = self.task_store.get_task(task_id)
        registered_task = self._registered_task(task_id)
        if stored_task is None or registered_task is None:
            return None
        registered_task.func(**self._task_kwargs(registered_task, stored_task))
        return self._with_runtime(stored_task)

    def is_available(self, task_id):
        registered_task = self._registered_task(task_id)
        return bool(registered_task and registered_task.is_available(self.context))

    def _sync_registered_tasks(self):
        overrides = {task.id: task.config_overrides() for task in TASK_REGISTRY}
        self.task_store.sync_registered_tasks(TASK_REGISTRY, overrides)

    def _load_jobs(self):
        for stored_task in self.task_store.list_tasks():
            registered_task = self._registered_task(stored_task["id"])
            if registered_task is None or self.scheduler.get_job(stored_task["id"]):
                continue
            try:
                job = self._add_job(registered_task, stored_task)
            except ConflictingIdError:
                continue
            if not stored_task.get("enabled", True):
                job.pause()

    def _update_job(self, stored_task):
        registered_task = self._registered_task(stored_task["id"])
        if registered_task is None:
            return
        enabled = stored_task.get("enabled", True)
        job = self.scheduler.get_job(stored_task["id"])
        if job is None:
            job = self._add_job(registered_task, stored_task)
        else:
            job.reschedule(**self._job_trigger(registered_task, stored_task))
            job.modify(kwargs=self._task_kwargs(registered_task, stored_task))
        job.resume() if enabled else job.pause()

    def _add_job(self, registered_task, stored_task):
        return self.scheduler.add_job(
            registered_task.func,
            id=registered_task.id,
            replace_existing=False,
            kwargs=self._task_kwargs(registered_task, stored_task),
            **self._job_trigger(registered_task, stored_task),
        )

    def _task_kwargs(self, registered_task, stored_task):
        return {
            **registered_task.kwargs,
            **stored_task.get("kwargs", {}),
            **registered_task.runtime_kwargs(self.context),
        }

    @staticmethod
    def _job_trigger(registered_task, stored_task):
        return {
            "trigger": "interval",
            "seconds": stored_task.get(
                "interval_seconds", registered_task.interval_seconds
            ),
        }

    def _with_runtime(self, task):
        job = self.scheduler.get_job(task.get("id"))
        next_run = getattr(job, "next_run_time", None) if job else None
        return {
            **task,
            "available": self.is_available(task.get("id")),
            "running": bool(next_run is not None),
        }

    @staticmethod
    def _registered_task(task_id):
        return next((task for task in TASK_REGISTRY if task.id == task_id), None)
