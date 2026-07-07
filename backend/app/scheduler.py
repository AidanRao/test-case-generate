from apscheduler.schedulers.background import BackgroundScheduler

TASK_HANDLERS = {}

scheduler = BackgroundScheduler(timezone="Asia/Shanghai")


def register_handler(task_type, func):
    TASK_HANDLERS[task_type] = func


def load_jobs_from_store(scheduler_instance, task_store):
    tasks = task_store.list_tasks()
    for task in tasks:
        if task["type"] not in TASK_HANDLERS:
            continue

        job = _add_interval_job(scheduler_instance, task)
        if not task.get("enabled", True):
            job.pause()


def update_job(scheduler_instance, task):
    task_id = task["id"]
    task_type = task["type"]
    enabled = task.get("enabled", True)

    if task_type not in TASK_HANDLERS:
        return False

    job = scheduler_instance.get_job(task_id)

    if job is None:
        job = _add_interval_job(scheduler_instance, task)
        if not enabled:
            job.pause()
    else:
        job.reschedule(trigger="interval", seconds=task["interval_seconds"])
        if enabled:
            job.resume()
        else:
            job.pause()
    return True


def _add_interval_job(scheduler_instance, task):
    return scheduler_instance.add_job(
        TASK_HANDLERS[task["type"]],
        trigger="interval",
        seconds=task["interval_seconds"],
        id=task["id"],
        replace_existing=True,
    )


def start_scheduler():
    if not scheduler.running:
        scheduler.start()


def shutdown_scheduler(wait=True):
    if scheduler.running:
        scheduler.shutdown(wait=wait)
