import os

from app.task_registry import scheduled_task


def _uniportal_sync_config():
    enabled = os.environ.get("UNIPORTAL_SYNC_ENABLED", "true").strip().lower()
    try:
        interval_seconds = int(os.environ.get("UNIPORTAL_SYNC_INTERVAL_SECONDS", "300"))
    except ValueError:
        interval_seconds = 300
    return {
        "enabled": enabled not in {"0", "false", "no", "off"},
        "interval_seconds": max(5, interval_seconds),
    }


def _uniportal_runtime_kwargs(storage):
    return {"storage": storage}


def _uniportal_available(storage):
    return storage.uniportal_source.enabled


@scheduled_task(
    id="uniportal_sync",
    name="UniPortal 项目同步",
    description="定期从 UniPortal 同步项目和需求数据",
    seconds=300,
    kwargs={"requirement_path": "document-validator/requirement.json"},
    config_factory=_uniportal_sync_config,
    runtime_kwargs_factory=_uniportal_runtime_kwargs,
    availability_check=_uniportal_available,
)
def synchronize_uniportal(storage, requirement_path):
    storage.synchronize_uniportal(requirement_path)
