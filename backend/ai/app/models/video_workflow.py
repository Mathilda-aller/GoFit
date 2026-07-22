from __future__ import annotations

from datetime import datetime, timezone
from enum import StrEnum

from pydantic import Field

from app.models.action_card import (
    ActionCardBuildRequest,
    ActionCardBuildResult,
    ContractModel,
    MediaKind,
    SourceVideo,
    StandardActionCandidate,
)


class WorkflowStage(StrEnum):
    QUEUED = "QUEUED"
    UNDERSTANDING_VIDEO = "UNDERSTANDING_VIDEO"
    LOCATING_CLIPS = "LOCATING_CLIPS"
    BUILDING_CARD = "BUILDING_CARD"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


class JobStatus(StrEnum):
    QUEUED = "QUEUED"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


def demo_lateral_raise_candidates() -> list[StandardActionCandidate]:
    """Return the one manually confirmed standard action used by the P0 demo."""
    return [
        StandardActionCandidate(
            standardActionId="action_lateral_raise",
            name="哑铃侧平举",
            aliases=["侧平举", "站姿哑铃侧平举"],
            bodyRegion="肩部",
            primaryMuscles=["三角肌中束"],
            secondaryMuscles=["三角肌前束"],
            equipment=["哑铃"],
        )
    ]


class VideoWorkflowRequest(ContractModel):
    request_id: str = Field(alias="requestId", min_length=1)
    source_video: SourceVideo = Field(alias="sourceVideo")
    video_path: str = Field(alias="videoPath", min_length=1)
    standard_action_candidates: list[StandardActionCandidate] = Field(
        alias="standardActionCandidates",
        default_factory=demo_lateral_raise_candidates,
        min_length=1,
    )


class TranscriptionSegment(ContractModel):
    start_ms: int = Field(alias="startMs", ge=0)
    end_ms: int = Field(alias="endMs", gt=0)
    text: str = Field(min_length=1)
    confidence: float | None = Field(default=None, ge=0, le=1)


class FrameObservation(ContractModel):
    observation_id: str = Field(alias="observationId", min_length=1)
    start_ms: int = Field(alias="startMs", ge=0)
    end_ms: int = Field(alias="endMs", gt=0)
    description: str = Field(min_length=1)
    on_screen_text: str | None = Field(alias="onScreenText", default=None)
    confidence: float | None = Field(default=None, ge=0, le=1)


class OcrObservation(ContractModel):
    timestamp_ms: int = Field(alias="timestampMs", ge=0)
    text: str = Field(min_length=1)
    confidence: float | None = Field(default=None, ge=0, le=1)


class OcrAnalysis(ContractModel):
    observations: list[OcrObservation] = Field(default_factory=list)


class MediaProposal(ContractModel):
    candidate_id: str = Field(alias="candidateId", min_length=1)
    kind: MediaKind
    start_ms: int = Field(alias="startMs", ge=0)
    end_ms: int = Field(alias="endMs", gt=0)
    observation_ids: list[str] = Field(alias="observationIds", min_length=1)


class VideoAnalysis(ContractModel):
    observations: list[FrameObservation] = Field(min_length=1)
    media_proposals: list[MediaProposal] = Field(
        alias="mediaProposals",
        default_factory=list,
    )


class MediaArtifact(ContractModel):
    candidate_id: str = Field(alias="candidateId", min_length=1)
    kind: MediaKind
    file_path: str = Field(alias="filePath", min_length=1)
    start_ms: int = Field(alias="startMs", ge=0)
    end_ms: int = Field(alias="endMs", gt=0)


class VideoWorkflowResult(ContractModel):
    request_id: str = Field(alias="requestId")
    action_card_request: ActionCardBuildRequest = Field(alias="actionCardRequest")
    action_card_result: ActionCardBuildResult = Field(alias="actionCardResult")
    media_artifacts: list[MediaArtifact] = Field(alias="mediaArtifacts")


class JobError(ContractModel):
    code: str
    message: str
    retryable: bool = False


class ActionCardJob(ContractModel):
    job_id: str = Field(alias="jobId")
    request_id: str = Field(alias="requestId")
    status: JobStatus
    stage: WorkflowStage
    progress: int = Field(ge=0, le=100)
    message: str
    result: VideoWorkflowResult | None = None
    error: JobError | None = None
    created_at: datetime = Field(
        alias="createdAt",
        default_factory=lambda: datetime.now(timezone.utc),
    )
    updated_at: datetime = Field(
        alias="updatedAt",
        default_factory=lambda: datetime.now(timezone.utc),
    )
