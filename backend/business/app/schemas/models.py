"""Public business API schemas."""

from __future__ import annotations

from typing import Any, Literal

from pydantic import Field

from app.schemas.common import ApiModel


FeedbackType = Literal[
    "TARGET_FELT",
    "OTHER_FELT",
    "NO_FEELING",
    "NO_CLEAR_FEELING",
    "TOO_HARD",
    "TOO_DIFFICULT",
    "DISCOMFORT",
]


class SourceVideo(ApiModel):
    id: str
    title: str
    creator_name: str
    source_url: str
    cover_url: str | None = None


class ExperienceSummary(ApiModel):
    exercise_id: str
    comment_count: int
    source_video_count: int


class ActionCard(ApiModel):
    id: str
    video_id: str
    exercise_id: str
    action_name: str
    body_region: str
    primary_muscles: list[str]
    secondary_muscles: list[str]
    equipment: list[str]
    status: str
    card_data: dict[str, Any]
    source_video: SourceVideo
    is_saved: bool = False
    experience_summary: ExperienceSummary | None = None


class ActionCardList(ApiModel):
    items: list[ActionCard]


class ImportVideoRequest(ApiModel):
    video_id: str | None = None
    title: str | None = None
    creator_name: str | None = None
    source_url: str | None = None
    asset_file_name: str | None = None


class ImportVideoResult(ApiModel):
    video_id: str
    task_id: str
    status: str
    card_id: str | None = None
    message: str
    media_url: str | None = None


class ProcessingStatus(ApiModel):
    task_id: str
    video_id: str
    status: str
    card_id: str | None = None
    error_message: str | None = None


class PlanItem(ApiModel):
    id: str
    card_id: str
    sort_order: int
    card: ActionCard


class TrainingPlan(ApiModel):
    id: str
    user_id: str
    name: str
    status: str
    item_count: int
    body_regions: list[str]
    card_names: list[str]
    created_at: str
    updated_at: str
    last_used_at: str | None
    use_count: int
    items: list[PlanItem] = Field(default_factory=list)


class ActiveSessionSummary(ApiModel):
    id: str
    plan_id: str
    plan_name: str
    status: str
    completed_count: int
    total_count: int
    started_at: str


class PlanList(ApiModel):
    active_session: ActiveSessionSummary | None
    items: list[TrainingPlan]


class CreatePlanRequest(ApiModel):
    name: str | None = None
    initial_card_id: str | None = None


class UpdatePlanRequest(ApiModel):
    name: str | None = None
    status: Literal["DRAFT", "SAVED", "ARCHIVED"] | None = None
    ordered_item_ids: list[str] | None = None


class AddPlanItemRequest(ApiModel):
    card_id: str


class SessionItem(ApiModel):
    id: str
    card_id: str
    sort_order: int
    item_status: str
    feedback_type: str | None
    felt_muscles: list[str]
    feedback_at: str | None
    card: ActionCard


class TrainingSession(ApiModel):
    id: str
    user_id: str
    plan_id: str
    plan_name: str
    status: str
    current_index: int
    started_at: str
    completed_at: str | None
    completed_count: int
    total_count: int
    items: list[SessionItem]


class UpdateSessionItemRequest(ApiModel):
    item_status: Literal["PENDING", "COMPLETED", "SKIPPED", "STOPPED_FOR_DISCOMFORT"] | None = None
    feedback_type: FeedbackType | None = None
    felt_muscles: list[str] | None = None


class SubmitFeedbackRequest(ApiModel):
    item_id: str
    feedback_type: FeedbackType
    felt_muscles: list[str] = Field(default_factory=list)


class FeedbackResult(ApiModel):
    session: TrainingSession
    problem_tag: str | None
    should_show_safety: bool
    next_item_id: str | None


class RecommendationItem(ApiModel):
    card: ActionCard
    reason_code: str
    reason_text: str


class RecommendationResult(ApiModel):
    request_id: str
    rule_version: str
    outcome_code: str
    items: list[RecommendationItem]


class ExperienceComment(ApiModel):
    id: str
    content: str
    author_name: str
    source_video: SourceVideo
    source_url: str | None = None


class ExperienceGroup(ApiModel):
    id: str
    method_name: str
    summary: str
    mention_count: int
    source_video_count: int
    has_disagreement: bool
    risk_type: str
    comments: list[ExperienceComment]


class ExperienceResult(ApiModel):
    exercise_id: str
    exercise_name: str
    problem_tag: str
    problem_title: str
    comment_count: int
    source_video_count: int
    source_note: str
    safety_triggered: bool
    groups: list[ExperienceGroup]


class MeSummary(ApiModel):
    user_id: str
    nickname: str
    completed_session_count: int
    completed_action_count: int
    recent_body_regions: list[str]
    recent_actions: list[str]
    has_discomfort_record: bool
