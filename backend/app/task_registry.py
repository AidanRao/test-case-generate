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
    config_factory: Callable[[], dict[str, Any]] | None
    runtime_kwargs_factory: Callable[[Any], dict[str, Any]] | None
    availability_check: Callable[[Any], bool] | None

    def config_overrides(self):
        return self.config_factory() if self.config_factory else {}

    def runtime_kwargs(self, context):
        if self.runtime_kwargs_factory:
            return self.runtime_kwargs_factory(context)
        return {}

    def is_available(self, context):
        return self.availability_check(context) if self.availability_check else True

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
            "kwargs": overrides.get("kwargs", self.kwargs),
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
    config_factory: Callable[[], dict[str, Any]] | None = None,
    runtime_kwargs_factory: Callable[[Any], dict[str, Any]] | None = None,
    availability_check: Callable[[Any], bool] | None = None,
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
                config_factory=config_factory,
                runtime_kwargs_factory=runtime_kwargs_factory,
                availability_check=availability_check,
            )
        )
        return func

    return decorator
