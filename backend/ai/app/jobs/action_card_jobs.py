from __future__ import annotations

from datetime import datetime, timezone
from threading import Lock

from app.errors import SkillError
from app.models.video_workflow import (
    ActionCardJob,
    JobError,
    JobStatus,
    VideoWorkflowRequest,
    WorkflowStage,
)
from app.workflows.fitness_video_reconstruction import FitnessVideoReconstructionWorkflow


class ActionCardJobService:
    """Small in-memory job runner for the local MVP."""

    def __init__(self, workflow: FitnessVideoReconstructionWorkflow) -> None:
        self.workflow = workflow
        self._jobs: dict[str, ActionCardJob] = {}
        self._lock = Lock()

    def create_job(self, request: VideoWorkflowRequest) -> tuple[ActionCardJob, bool]:
        with self._lock:
            existing = self._jobs.get(request.request_id)
            if existing is not None:
                return existing.model_copy(deep=True), False
            job = ActionCardJob(
                jobId=request.request_id,
                requestId=request.request_id,
                status=JobStatus.QUEUED,
                stage=WorkflowStage.QUEUED,
                progress=0,
                message="任务已创建",
            )
            self._jobs[job.job_id] = job
            return job.model_copy(deep=True), True

    def run_job(self, job_id: str, request: VideoWorkflowRequest) -> None:
        self._update(
            job_id,
            status=JobStatus.RUNNING,
            stage=WorkflowStage.UNDERSTANDING_VIDEO,
            progress=5,
            message="正在理解视频内容",
        )
        try:
            result = self.workflow.execute(
                request,
                on_progress=lambda stage, progress, message: self._update(
                    job_id,
                    status=JobStatus.RUNNING,
                    stage=stage,
                    progress=progress,
                    message=message,
                ),
            )
            self._update(
                job_id,
                status=JobStatus.COMPLETED,
                stage=WorkflowStage.COMPLETED,
                progress=100,
                message="动作卡已生成",
                result=result,
                error=None,
            )
        except SkillError as exc:
            self._update(
                job_id,
                status=JobStatus.FAILED,
                stage=WorkflowStage.FAILED,
                message=exc.message,
                error=JobError(
                    code=exc.code,
                    message=exc.message,
                    retryable=exc.retryable,
                ),
            )
        except Exception:
            self._update(
                job_id,
                status=JobStatus.FAILED,
                stage=WorkflowStage.FAILED,
                message="视频处理失败，未暴露内部异常。",
                error=JobError(
                    code="VIDEO_WORKFLOW_FAILED",
                    message="视频处理失败，未暴露内部异常。",
                ),
            )

    def get_job(self, job_id: str) -> ActionCardJob:
        with self._lock:
            job = self._jobs.get(job_id)
            if job is None:
                raise SkillError(
                    "ACTION_CARD_JOB_NOT_FOUND",
                    "找不到这个视频处理任务。",
                    request_id=job_id,
                )
            return job.model_copy(deep=True)

    def _update(self, job_id: str, **changes) -> None:
        with self._lock:
            current = self._jobs[job_id]
            changes["updated_at"] = datetime.now(timezone.utc)
            self._jobs[job_id] = current.model_copy(update=changes)

