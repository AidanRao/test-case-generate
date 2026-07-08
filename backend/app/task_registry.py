from dataclasses import dataclass
from typing import Any, Callable


@dataclass
class ScheduledTask:
    id: str
    func: Callable
    interval_seconds: int
    kwargs: dict[str, Any]
    name: str
    description: str
    enabled: bool

    def to_store_record(self, overrides=None):
        overrides = overrides or {}
        return {
            "id": self.id,
            "name": overrides.get("name", self.name),
            "description": overrides.get("description", self.description),
            "enabled": overrides.get("enabled", self.enabled),
            "interval_seconds": int(
                overrides.get("interval_seconds", self.interval_seconds)
            ),
        }


TASK_REGISTRY: list[ScheduledTask] = []


def scheduled_task(
    *,
    id: str,
    seconds: int,
    name: str = "",
    description: str = "",
    enabled: bool = True,
    kwargs: dict[str, Any] | None = None,
):
    def decorator(func: Callable):
        TASK_REGISTRY.append(
            ScheduledTask(
                id=id,
                func=func,
                interval_seconds=int(seconds),
                kwargs=kwargs or {},
                name=name,
                description=description,
                enabled=enabled,
            )
        )
        return func

    return decorator
