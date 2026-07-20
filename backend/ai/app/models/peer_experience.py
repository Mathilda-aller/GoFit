from __future__ import annotations

from enum import StrEnum

from pydantic import Field

from app.models.action_card import ContractModel
from app.models.recommendation import FeedbackType


class CommentRiskType(StrEnum):
    NORMAL = "NORMAL"
    HEALTH_RISK = "HEALTH_RISK"
    DANGEROUS_ADVICE = "DANGEROUS_ADVICE"
    ABUSE_OR_SPAM = "ABUSE_OR_SPAM"


class DigestStatus(StrEnum):
    SUFFICIENT = "SUFFICIENT"
    INSUFFICIENT = "INSUFFICIENT"
    DEGRADED = "DEGRADED"


class MockPeerComment(ContractModel):
    comment_id: str = Field(alias="id", min_length=1)
    video_id: str = Field(alias="videoId", min_length=1)
    text: str = Field(min_length=1)
    risk_type: CommentRiskType = Field(alias="riskType")
    problem_tag: str = Field(alias="problemTag", min_length=1)


class StandardActionRef(ContractModel):
    action_id: str = Field(alias="id", min_length=1)
    name: str = Field(min_length=1)


class PeerExperienceDigestRequest(ContractModel):
    request_id: str = Field(alias="requestId", min_length=1)
    standard_action: StandardActionRef = Field(alias="standardAction")
    comments: list[MockPeerComment] = Field(min_length=1)


class PeerExperienceCluster(ContractModel):
    cluster_id: str = Field(alias="clusterId", min_length=1)
    problem_tag: str = Field(alias="problemTag", min_length=1)
    method_name: str = Field(alias="methodName", min_length=1)
    summary: str = Field(min_length=1)
    mention_count: int = Field(alias="mentionCount", ge=1)
    source_video_count: int = Field(alias="sourceVideoCount", ge=1)
    comment_ids: list[str] = Field(alias="commentIds", min_length=1)
    has_disagreement: bool = Field(alias="hasDisagreement")
    risk_type: CommentRiskType = Field(alias="riskType")


class PeerExperienceDigestResult(ContractModel):
    request_id: str = Field(alias="requestId", min_length=1)
    standard_action_id: str = Field(alias="standardActionId", min_length=1)
    status: DigestStatus
    clusters: list[PeerExperienceCluster]
    excluded_comment_ids: list[str] = Field(alias="excludedCommentIds")
    provider_mode: str = Field(alias="providerMode", min_length=1)


class AvailablePeerCluster(ContractModel):
    cluster_id: str = Field(alias="clusterId", min_length=1)
    problem_tag: str = Field(alias="problemTag", min_length=1)


class PeerExperienceMatchRequest(ContractModel):
    request_id: str = Field(alias="requestId", min_length=1)
    standard_action_id: str = Field(alias="standardActionId", min_length=1)
    feedback_type: FeedbackType = Field(alias="feedbackType")
    felt_muscles: list[str] = Field(alias="feltMuscles", default_factory=list)
    available_clusters: list[AvailablePeerCluster] = Field(
        alias="availableClusters",
        default_factory=list,
    )


class PeerExperienceMatchResult(ContractModel):
    request_id: str = Field(alias="requestId", min_length=1)
    problem_tag: str | None = Field(alias="problemTag")
    matched_cluster_ids: list[str] = Field(alias="matchedClusterIds")
    safety_route: bool = Field(alias="safetyRoute")
