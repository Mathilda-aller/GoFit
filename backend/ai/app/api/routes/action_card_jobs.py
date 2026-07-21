from functools import lru_cache

from fastapi import APIRouter, BackgroundTasks, Depends, Response, status

from app.core.config import get_settings
from app.jobs.action_card_jobs import ActionCardJobService
from app.models.video_workflow import ActionCardJob, VideoWorkflowRequest
from app.workflows.factory import build_video_workflow


router = APIRouter(tags=["action-card-jobs"])


@lru_cache
def get_job_service() -> ActionCardJobService:
    return ActionCardJobService(build_video_workflow(get_settings()))


@router.post(
    "/action-card-jobs",
    response_model=ActionCardJob,
    status_code=status.HTTP_202_ACCEPTED,
)
def create_action_card_job(
    request: VideoWorkflowRequest,
    background_tasks: BackgroundTasks,
    response: Response,
    service: ActionCardJobService = Depends(get_job_service),
) -> ActionCardJob:
    job, created = service.create_job(request)
    if created:
        background_tasks.add_task(service.run_job, job.job_id, request)
    else:
        response.headers["X-GoFit-Idempotent-Replay"] = "true"
    return job


@router.get("/action-card-jobs/{job_id}", response_model=ActionCardJob)
def get_action_card_job(
    job_id: str,
    service: ActionCardJobService = Depends(get_job_service),
) -> ActionCardJob:
    return service.get_job(job_id)

