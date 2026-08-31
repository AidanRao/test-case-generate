import time
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
from threading import RLock

from app.services.errors import BusinessError
from app.services.testcase_service import TestCaseGenerationError, TestCaseService
from app.utils.ids import new_uuid


ACTIVE_STATUSES = frozenset({"pending", "running"})


@dataclass
class TestCaseGenerationJob:
    id: str
    project_id: str
    requirement_ids: tuple[str, ...]
    status: str = "pending"
    created_at: float = field(default_factory=time.time)
    started_at: float | None = None
    finished_at: float | None = None
    processing_requirement_ids: list[str] = field(default_factory=list)
    completed_requirement_ids: list[str] = field(default_factory=list)
    failed_requirement_ids: list[str] = field(default_factory=list)
    error: str | None = None

    @property
    def active(self):
        return self.status in ACTIVE_STATUSES

    def to_dict(self):
        completed_ids = set(self.completed_requirement_ids)
        failed_ids = set(self.failed_requirement_ids)
        processing_ids = set(self.processing_requirement_ids)
        active_requirement_ids = (
            [
                requirement_id
                for requirement_id in self.requirement_ids
                if requirement_id not in completed_ids
                and requirement_id not in failed_ids
            ]
            if self.active
            else []
        )
        return {
            "job_id": self.id,
            "project_id": self.project_id,
            "requirement_ids": list(self.requirement_ids),
            "active_requirement_ids": active_requirement_ids,
            "status": self.status,
            "active": self.active,
            "created_at": self.created_at,
            "started_at": self.started_at,
            "finished_at": self.finished_at,
            "processing_requirement_ids": [
                requirement_id
                for requirement_id in self.requirement_ids
                if requirement_id in processing_ids
            ],
            "completed_requirement_ids": list(self.completed_requirement_ids),
            "failed_requirement_ids": list(self.failed_requirement_ids),
            "completed_count": len(self.completed_requirement_ids),
            "failed_count": len(self.failed_requirement_ids),
            "processed_count": (
                len(self.completed_requirement_ids)
                + len(self.failed_requirement_ids)
            ),
            "total_count": len(self.requirement_ids),
            "error": self.error,
        }


class TestCaseJobManager:
    def __init__(self, storage, config, max_workers=4, max_history=1000):
        self._storage = storage
        self._config = config
        self._lock = RLock()
        self._jobs = {}
        self._active_job_by_project = {}
        self._max_history = max(1, int(max_history))
        self._executor = ThreadPoolExecutor(
            max_workers=max(1, int(max_workers)),
            thread_name_prefix="testcase-generation",
        )

    def submit(self, project_id, requirement_ids=None, replace=False, ai_config=None):
        project_id = str(project_id)
        if not self._storage.get_project(project_id):
            raise BusinessError(40401, "资源不存在", 404)
        requirements = self._storage.list_requirements(project_id) or []
        by_id = {str(item["id"]): item for item in requirements if item.get("id")}
        if requirement_ids is None:
            selected = list(by_id)
        elif isinstance(requirement_ids, list):
            if not all(isinstance(item, str) and item.strip() for item in requirement_ids):
                raise BusinessError(40001, "requirement_ids 只能包含非空字符串")
            selected = list(dict.fromkeys(item.strip() for item in requirement_ids))
        else:
            raise BusinessError(40001, "requirement_ids 必须是数组")
        if not selected:
            raise BusinessError(40001, "没有可生成测试用例的需求")
        if any(requirement_id not in by_id for requirement_id in selected):
            raise BusinessError(40401, "需求不存在", 404)
        requirement_snapshots = tuple(
            {**by_id[requirement_id], "id": requirement_id}
            for requirement_id in selected
        )
        normalized_ids = tuple(selected)
        with self._lock:
            active_job_id = self._active_job_by_project.get(project_id)
            if active_job_id:
                raise BusinessError(
                    40901, "该项目已有测试用例生成任务正在进行", 409,
                    self._jobs[active_job_id].to_dict(),
                )

            job = TestCaseGenerationJob(
                id=new_uuid(),
                project_id=project_id,
                requirement_ids=normalized_ids,
            )
            self._jobs[job.id] = job
            self._active_job_by_project[project_id] = job.id
            self._prune_history_locked()
            job_data = job.to_dict()

        self._executor.submit(
            self._run,
            job.id,
            requirement_snapshots,
            replace,
            ai_config,
        )
        return job_data

    def get_job(self, job_id):
        with self._lock:
            job = self._jobs.get(str(job_id))
            return job.to_dict() if job else None

    def get_project_job(self, project_id, job_id):
        job = self.get_job(job_id)
        if not job or str(job["project_id"]) != str(project_id):
            raise BusinessError(40401, "资源不存在", 404)
        return job

    def get_project_status(self, project_id):
        project_id = str(project_id)
        if not self._storage.get_project(project_id):
            raise BusinessError(40401, "资源不存在", 404)
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
                "active_requirement_ids": [],
                "status": "idle",
                "active": False,
                "created_at": None,
                "started_at": None,
                "finished_at": None,
                "processing_requirement_ids": [],
                "completed_requirement_ids": [],
                "failed_requirement_ids": [],
                "completed_count": 0,
                "failed_count": 0,
                "processed_count": 0,
                "total_count": 0,
                "error": None,
            }

    def has_active_project(self, project_id):
        with self._lock:
            return str(project_id) in self._active_job_by_project

    def ensure_not_generating(self, project_id):
        if self.has_active_project(project_id):
            raise BusinessError(
                40902, "测试用例生成期间不能修改项目数据", 409,
                self.get_project_status(project_id),
            )

    def shutdown(self, wait=False):
        self._executor.shutdown(wait=wait, cancel_futures=False)

    def _run(self, job_id, requirements, replace, ai_config):
        self._mark_running(job_id)
        job = self.get_job(job_id)
        if not job:
            return

        service = TestCaseService(self._storage, self._config)
        try:
            service.generate_testcases(
                job["project_id"],
                requirements,
                replace=replace,
                ai_config=ai_config,
                on_requirement_started=lambda requirement_id: self._mark_requirement_started(
                    job_id, requirement_id
                ),
                on_requirement_finished=lambda requirement_id: self._mark_requirement_finished(
                    job_id, requirement_id
                ),
                on_requirement_completed=lambda requirement_id: self._mark_requirement_completed(
                    job_id, requirement_id
                ),
                on_requirement_failed=lambda requirement_id: self._mark_requirement_failed(
                    job_id, requirement_id
                ),
            )
        except TestCaseGenerationError as exc:
            self._finish(job_id, "failed", exc.code)
        except Exception as exc:
            self._finish(job_id, "failed", f"internal_error:{exc.__class__.__name__}")
        else:
            self._finish(job_id, "completed")

    def _mark_running(self, job_id):
        with self._lock:
            job = self._jobs.get(job_id)
            if not job or not job.active:
                return
            job.status = "running"
            job.started_at = time.time()

    def _mark_requirement_started(self, job_id, requirement_id):
        requirement_id = str(requirement_id)
        with self._lock:
            job = self._jobs.get(job_id)
            if (
                job
                and job.active
                and requirement_id not in job.processing_requirement_ids
            ):
                job.processing_requirement_ids.append(requirement_id)

    def _mark_requirement_finished(self, job_id, requirement_id):
        requirement_id = str(requirement_id)
        with self._lock:
            job = self._jobs.get(job_id)
            if not job or not job.active:
                return
            if requirement_id in job.processing_requirement_ids:
                job.processing_requirement_ids.remove(requirement_id)

    def _mark_requirement_completed(self, job_id, requirement_id):
        requirement_id = str(requirement_id)
        with self._lock:
            job = self._jobs.get(job_id)
            if not job or not job.active:
                return
            if requirement_id in job.processing_requirement_ids:
                job.processing_requirement_ids.remove(requirement_id)
            if requirement_id not in job.completed_requirement_ids:
                job.completed_requirement_ids.append(requirement_id)

    def _mark_requirement_failed(self, job_id, requirement_id):
        requirement_id = str(requirement_id)
        with self._lock:
            job = self._jobs.get(job_id)
            if not job or not job.active:
                return
            if requirement_id in job.processing_requirement_ids:
                job.processing_requirement_ids.remove(requirement_id)
            if requirement_id not in job.failed_requirement_ids:
                job.failed_requirement_ids.append(requirement_id)

    def _finish(self, job_id, status, error=None):
        with self._lock:
            job = self._jobs.get(job_id)
            if not job:
                return
            if status == "failed":
                processed_ids = set(job.completed_requirement_ids)
                processed_ids.update(job.failed_requirement_ids)
                for requirement_id in job.requirement_ids:
                    if requirement_id not in processed_ids:
                        job.failed_requirement_ids.append(requirement_id)
            job.status = status
            job.error = error
            job.processing_requirement_ids.clear()
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
