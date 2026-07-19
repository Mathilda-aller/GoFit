from __future__ import annotations

from enum import StrEnum

from pydantic import Field

from app.models.action_card import ContractModel


class FeedbackType(StrEnum):
    TARGET_FELT = "TARGET_FELT"
    OTHER_FELT = "OTHER_FELT"
    NO_FEELING = "NO_FEELING"
    NO_CLEAR_FEELING = "NO_CLEAR_FEELING"
    TOO_HARD = "TOO_HARD"
    TOO_DIFFICULT = "TOO_DIFFICULT"
    DISCOMFORT = "DISCOMFORT"


class RecommendationReasonCode(StrEnum):
    HISTORY_TARGET_FELT = "HISTORY_TARGET_FELT"
    MUSCLE_COVERAGE_COMPLEMENT = "MUSCLE_COVERAGE_COMPLEMENT"
    SAME_BODY_REGION = "SAME_BODY_REGION"
    SAVED_NOT_TRIED = "SAVED_NOT_TRIED"


class RecommendationOutcomeCode(StrEnum):
    OK = "OK"
    NO_SAFE_CANDIDATE = "NO_SAFE_CANDIDATE"


class CurrentWorkoutItem(ContractModel):
    action_card_id: str = Field(alias="actionCardId", min_length=1)
    body_region: str | None = Field(alias="bodyRegion", default=None, min_length=1)
    primary_muscles: list[str] = Field(alias="primaryMuscles", min_length=1)


class RecommendationCandidate(ContractModel):
    # Candidate fields are intentionally nullable. A malformed candidate must be
    # skipped without rejecting other usable candidates in the same request.
    action_card_id: str | None = Field(alias="actionCardId", default=None)
    body_region: str | None = Field(alias="bodyRegion", default=None)
    primary_muscles: list[str] | None = Field(alias="primaryMuscles", default=None)
    secondary_muscles: list[str] | None = Field(alias="secondaryMuscles", default=None)
    is_saved: bool | None = Field(alias="isSaved", default=None)
    has_tried: bool | None = Field(alias="hasTried", default=None)
    content_ready: bool | None = Field(alias="contentReady", default=None)
    source_risk: bool | None = Field(alias="sourceRisk", default=None)


class RecommendationHistoryItem(ContractModel):
    action_card_id: str = Field(alias="actionCardId", min_length=1)
    feedback_type: FeedbackType = Field(alias="feedbackType")


class RecommendationRankRequest(ContractModel):
    request_id: str = Field(alias="requestId", min_length=1)
    selected_body_region: str | None = Field(
        alias="selectedBodyRegion",
        default=None,
        min_length=1,
    )
    current_items: list[CurrentWorkoutItem] = Field(
        alias="currentItems",
        default_factory=list,
    )
    candidates: list[RecommendationCandidate] = Field(default_factory=list)
    history: list[RecommendationHistoryItem] = Field(default_factory=list)
    excluded_action_card_ids: list[str] = Field(
        alias="excludedActionCardIds",
        default_factory=list,
    )


class RecommendationItem(ContractModel):
    action_card_id: str = Field(alias="actionCardId", min_length=1)
    reason_code: RecommendationReasonCode = Field(alias="reasonCode")
    reason_text: str = Field(alias="reasonText", min_length=1)


class RecommendationRankResult(ContractModel):
    request_id: str = Field(alias="requestId", min_length=1)
    rule_version: str = Field(alias="ruleVersion", min_length=1)
    outcome_code: RecommendationOutcomeCode = Field(alias="outcomeCode")
    items: list[RecommendationItem] = Field(max_length=3)
