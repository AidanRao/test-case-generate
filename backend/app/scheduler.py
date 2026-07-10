from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.jobstores.base import ConflictingIdError

from app.task_registry import TASK_REGISTRY

scheduler = BackgroundScheduler(timezone="Asia/Shanghai")
RUNTIME_KWARGS = {}


def sync_default_jobs(
    scheduler_instance,
    task_store,
    runtime_kwargs=None,
    default_overrides=None,
):
    import app.tasks  # noqa: F401

    global RUNTIME_KWARGS
    RUNTIME_KWARGS = runtime_kwargs or {}
    task_store.sync_registered_tasks(TASK_REGISTRY, default_overrides)
    load_jobs_from_store(scheduler_instance, task_store, RUNTIME_KWARGS)


def load_jobs_from_store(scheduler_instance, task_store, runtime_kwargs=None):
    runtime_kwargs = runtime_kwargs or {}
    tasks = task_store.list_tasks()
    for task in tasks:
        registered_task = _registered_task(task["id"])
        if registered_task is None:
            continue
        if scheduler_instance.get_job(task["id"]) is not None:
            continue

        try:
            job = _add_job(scheduler_instance, registered_task, task, runtime_kwargs)
        except ConflictingIdError:
            continue
        if not task.get("enabled", True):
            job.pause()


def update_job(scheduler_instance, task):
    task_id = task["id"]
    enabled = task.get("enabled", True)
    registered_task = _registered_task(task_id)

    if registered_task is None:
        return False

    job = scheduler_instance.get_job(task_id)

    if job is None:
        job = _add_job(scheduler_instance, registered_task, task, RUNTIME_KWARGS)
        if not enabled:
            job.pause()
    else:
        job.reschedule(**_job_trigger(registered_task, task))
        job.modify(kwargs=_task_kwargs(registered_task, task, RUNTIME_KWARGS))
        if enabled:
            job.resume()
        else:
            job.pause()
    return True


def _registered_task(task_id):
    import app.tasks  # noqa: F401

    return next((task for task in TASK_REGISTRY if task.id == task_id), None)


def execute_task(task_id, stored_task, runtime_kwargs=None):
    registered_task = _registered_task(task_id)
    if registered_task is None:
        return False
    registered_task.func(
        **_task_kwargs(registered_task, stored_task, runtime_kwargs or {})
    )
    return True


def _add_job(scheduler_instance, registered_task, stored_task, runtime_kwargs=None):
    runtime_kwargs = runtime_kwargs or {}
    return scheduler_instance.add_job(
        registered_task.func,
        id=registered_task.id,
        replace_existing=False,
        kwargs=_task_kwargs(registered_task, stored_task, runtime_kwargs),
        **_job_trigger(registered_task, stored_task),
    )


def _task_kwargs(registered_task, stored_task, runtime_kwargs=None):
    runtime_kwargs = runtime_kwargs or {}
    return {
        **registered_task.kwargs,
        **stored_task.get("kwargs", {}),
        **runtime_kwargs.get(registered_task.id, {}),
    }


def _job_trigger(registered_task, stored_task):
    return {
        "trigger": "interval",
        "seconds": stored_task.get(
            "interval_seconds", registered_task.interval_seconds
        ),
    }


def start_scheduler():
    if not scheduler.running:
        scheduler.start()


def shutdown_scheduler(wait=True):
    if scheduler.running:
        scheduler.shutdown(wait=wait)
