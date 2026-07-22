from __future__ import annotations

from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field, model_validator


class ContractModel(BaseModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)


class EvidenceKind(StrEnum):
    ASR = "ASR"
    OCR = "OCR"
    VISION = "VISION"


class MediaKind(StrEnum):
    POSTER = "POSTER"
    CORRECT_DEMO = "CORRECT_DEMO"
    ERROR_DEMO = "ERROR_DEMO"


class BuildStatus(StrEnum):
    READY = "READY"
    NEEDS_REVIEW = "NEEDS_REVIEW"
    FAILED = "FAILED"


class MatchDecision(StrEnum):
    MATCHED = "MATCHED"
    NEEDS_REVIEW = "NEEDS_REVIEW"


class SourceVideo(ContractModel):
    video_id: str = Field(alias="videoId", min_length=1)
    title: str = Field(min_length=1)
    creator_name: str = Field(alias="creatorName", min_length=1)
    source_url: str = Field(alias="sourceUrl", min_length=1)


class TimedEvidence(ContractModel):
    evidence_id: str = Field(alias="evidenceId", min_length=1)
    kind: EvidenceKind
    start_ms: int = Field(alias="startMs", ge=0)
    end_ms: int = Field(alias="endMs", gt=0)
    text: str = Field(min_length=1)
    confidence: float | None = Field(default=None, ge=0, le=1)

    @model_validator(mode="after")
    def validate_range(self) -> "TimedEvidence":
        if self.end_ms <= self.start_ms:
            raise ValueError("endMs must be greater than startMs")
        return self


class StandardActionCandidate(ContractModel):
    standard_action_id: str = Field(alias="standardActionId", min_length=1)
    name: str = Field(min_length=1)
    aliases: list[str] = Field(default_factory=list)
    body_region: str = Field(alias="bodyRegion", min_length=1)
    primary_muscles: list[str] = Field(alias="primaryMuscles", min_length=1)
    secondary_muscles: list[str] = Field(alias="secondaryMuscles", default_factory=list)
    equipment: list[str] = Field(default_factory=list)


class MediaCandidate(ContractModel):
    candidate_id: str = Field(alias="candidateId", min_length=1)
    kind: MediaKind
    start_ms: int = Field(alias="startMs", ge=0)
    end_ms: int = Field(alias="endMs", gt=0)
    evidence_ids: list[str] = Field(alias="evidenceIds", min_length=1)

    @model_validator(mode="after")
    def validate_range(self) -> "MediaCandidate":
        if self.end_ms <= self.start_ms:
            raise ValueError("endMs must be greater than startMs")
        return self


class ActionCardBuildRequest(ContractModel):
    request_id: str = Field(alias="requestId", min_length=1)
    source_video: SourceVideo = Field(alias="sourceVideo")
    standard_action_candidates: list[StandardActionCandidate] = Field(
        alias="standardActionCandidates",
        min_length=1,
    )
    evidence: list[TimedEvidence] = Field(min_length=1)
    media_candidates: list[MediaCandidate] = Field(
        alias="mediaCandidates",
        default_factory=list,
    )


class EvidenceBoundText(ContractModel):
    text: str = Field(min_length=1)
    evidence_ids: list[str] = Field(alias="evidenceIds", min_length=1)


class ActionStep(ContractModel):
    order: int = Field(ge=1, le=5)
    instruction: str = Field(min_length=1)
    start_ms: int = Field(alias="startMs", ge=0)
    end_ms: int = Field(alias="endMs", gt=0)
    evidence_ids: list[str] = Field(alias="evidenceIds", min_length=1)

    @model_validator(mode="after")
    def validate_range(self) -> "ActionStep":
        if self.end_ms <= self.start_ms:
            raise ValueError("endMs must be greater than startMs")
        return self


class StandardActionMatch(ContractModel):
    standard_action_id: str = Field(alias="standardActionId", min_length=1)
    confidence: float = Field(ge=0, le=1)
    decision: MatchDecision


class MediaSelection(ContractModel):
    kind: MediaKind
    candidate_id: str = Field(alias="candidateId", min_length=1)
    start_ms: int = Field(alias="startMs", ge=0)
    end_ms: int = Field(alias="endMs", gt=0)
    evidence_ids: list[str] = Field(alias="evidenceIds", min_length=1)

    @model_validator(mode="after")
    def validate_range(self) -> "MediaSelection":
        if self.end_ms <= self.start_ms:
            raise ValueError("endMs must be greater than startMs")
        return self


class CommonError(ContractModel):
    mistake: str = Field(min_length=1)
    correction: str = Field(min_length=1)
    error_demo: MediaSelection = Field(alias="errorDemo")
    evidence_ids: list[str] = Field(alias="evidenceIds", min_length=1)


class LearningSide(ContractModel):
    correct_demo: MediaSelection | None = Field(alias="correctDemo", default=None)
    steps: list[ActionStep] = Field(min_length=3, max_length=5)
    key_reminders: list[EvidenceBoundText] = Field(
        alias="keyReminders",
        max_length=2,
    )
    common_errors: list[CommonError] = Field(
        alias="commonErrors",
        default_factory=list,
    )


class TrainingSide(ContractModel):
    loop_demo: MediaSelection | None = Field(alias="loopDemo", default=None)
    quick_cue: EvidenceBoundText = Field(alias="quickCue")
    quick_tips: list[EvidenceBoundText] = Field(alias="quickTips", max_length=3)


class ActionCard(ContractModel):
    source_video: SourceVideo = Field(alias="sourceVideo")
    action_name: str = Field(alias="actionName", min_length=1)
    body_region: str = Field(alias="bodyRegion", min_length=1)
    primary_muscles: list[str] = Field(alias="primaryMuscles", min_length=1)
    secondary_muscles: list[str] = Field(alias="secondaryMuscles", default_factory=list)
    equipment: list[str] = Field(default_factory=list)
    learning_side: LearningSide = Field(alias="learningSide")
    training_side: TrainingSide = Field(alias="trainingSide")


class ProviderInfo(ContractModel):
    name: str = Field(min_length=1)
    version: str = Field(min_length=1)


class ActionCardBuildResult(ContractModel):
    schema_version: str = Field(alias="schemaVersion", min_length=1)
    request_id: str = Field(alias="requestId", min_length=1)
    status: BuildStatus
    standard_action: StandardActionMatch = Field(alias="standardAction")
    action_card: ActionCard = Field(alias="actionCard")
    warnings: list[str] = Field(default_factory=list)
    needs_review_reasons: list[str] = Field(alias="needsReviewReasons", default_factory=list)
    provider: ProviderInfo
