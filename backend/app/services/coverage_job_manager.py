import time
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
from threading import RLock

from app.services.coverage_service import CoverageAnalysisError, CoverageService
from app.utils.ids import new_uuid


ACTIVE_STATUSES = frozenset({"pending", "running"})


@dataclass
class CoverageCalculationJob:
    id: str
    project_id: str
    requirement_ids: tuple[str, ...]
    status: str = "pending"
    created_at: float = field(default_factory=time.time)
    started_at: float | None = None
    finished_at: float | None = None
    completed_requirement_ids: list[str] = field(default_factory=list)
    error: str | None = None

    @property
    def active(self):
        return self.status in ACTIVE_STATUSES

    def to_dict(self):
        return {
            "job_id": self.id,
            "project_id": self.project_id,
            "requirement_ids": list(self.requirement_ids),
            "status": self.status,
            "active": self.active,
            "created_at": self.created_at,
            "started_at": self.started_at,
            "finished_at": self.finished_at,
            "completed_requirement_ids": list(self.completed_requirement_ids),
            "completed_count": len(self.completed_requirement_ids),
            "total_count": len(self.requirement_ids),
            "error": self.error,
        }


class CoverageJobManager:
    def __init__(self, storage, config, max_workers=2, max_history=1000):
        self._storage = storage
        self._config = config
        self._lock = RLock()
        self._jobs = {}
        self._active_job_by_project = {}
        self._max_history = max(1, int(max_history))
        self._executor = ThreadPoolExecutor(
            max_workers=max(1, int(max_workers)),
            thread_name_prefix="coverage-calculation",
        )

    def submit(self, project_id, requirements):
        project_id = str(project_id)
        requirement_ids = tuple(
            dict.fromkeys(
                str(requirement.get("id") or "").strip()
                for requirement in requirements
                if str(requirement.get("id") or "").strip()
            )
        )
        if not requirement_ids:
            raise ValueError("at least one requirement is required")

        with self._lock:
            active_job_id = self._active_job_by_project.get(project_id)
            if active_job_id:
                return None, self._jobs[active_job_id].to_dict()

            job = CoverageCalculationJob(
                id=new_uuid(),
                project_id=project_id,
                requirement_ids=requirement_ids,
            )
            self._jobs[job.id] = job
            self._active_job_by_project[project_id] = job.id
            self._prune_history_locked()
            job_data = job.to_dict()

        self._executor.submit(self._run, job.id)
        return job_data, None

    def get_job(self, job_id):
        with self._lock:
            job = self._jobs.get(str(job_id))
            return job.to_dict() if job else None

    def get_project_status(self, project_id):
        project_id = str(project_id)
        with self._lock:
            active_job_id = self._active_job_by_project.get(project_id)
            if active_job_id:
                return self._jobs[active_job_id].to_dict()

            latest = max(
                (
                    job
                    for job in self._jobs.values()
                    if job.project_id == project_id
                ),
                key=lambda job: job.created_at,
                default=None,
            )
            if latest:
                return latest.to_dict()
            return {
                "job_id": None,
                "project_id": project_id,
                "requirement_ids": [],
                "status": "idle",
                "active": False,
                "created_at": None,
                "started_at": None,
                "finished_at": None,
                "completed_requirement_ids": [],
                "completed_count": 0,
                "total_count": 0,
                "error": None,
            }

    def has_active_project(self, project_id):
        with self._lock:
            return str(project_id) in self._active_job_by_project

    def shutdown(self, wait=False):
        self._executor.shutdown(wait=wait, cancel_futures=False)

    def _run(self, job_id):
        self._mark_running(job_id)
        job = self.get_job(job_id)
        if not job:
            return

        service = CoverageService(self._storage, self._config)
        try:
            service.calculate_coverage(
                job["project_id"],
                on_requirement_completed=lambda requirement_id: (
                    self._mark_requirement_completed(job_id, requirement_id)
                ),
            )
        except CoverageAnalysisError as exc:
            self._finish(job_id, "failed", exc.code)
        except Exception as exc:
            self._finish(
                job_id,
                "failed",
                f"internal_error:{exc.__class__.__name__}",
            )
        else:
            self._finish(job_id, "completed")

    def _mark_running(self, job_id):
        with self._lock:
            job = self._jobs.get(job_id)
            if not job or not job.active:
                return
            job.status = "running"
            job.started_at = time.time()

    def _mark_requirement_completed(self, job_id, requirement_id):
        requirement_id = str(requirement_id)
        with self._lock:
            job = self._jobs.get(job_id)
            if not job or not job.active:
                return
            if requirement_id not in job.completed_requirement_ids:
                job.completed_requirement_ids.append(requirement_id)

    def _finish(self, job_id, status, error=None):
        with self._lock:
            job = self._jobs.get(job_id)
            if not job:
                return
            job.status = status
            job.error = error
            job.finished_at = time.time()
            if self._active_job_by_project.get(job.project_id) == job.id:
                self._active_job_by_project.pop(job.project_id, None)

    def _prune_history_locked(self):
        overflow = len(self._jobs) - self._max_history
        if overflow <= 0:
            return
        removable = sorted(
            (job for job in self._jobs.values() if not job.active),
            key=lambda job: job.created_at,
        )
        for job in removable[:overflow]:
            self._jobs.pop(job.id, None)
