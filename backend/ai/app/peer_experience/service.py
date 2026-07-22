from __future__ import annotations

from collections import defaultdict
import re

from sklearn.cluster import AgglomerativeClustering

from app.errors import SkillError
from app.models.peer_experience import (
    CommentRiskType,
    DigestStatus,
    MockPeerComment,
    PeerExperienceCluster,
    PeerExperienceDigestRequest,
    PeerExperienceDigestResult,
    PeerExperienceMatchRequest,
    PeerExperienceMatchResult,
)
from app.models.recommendation import FeedbackType
from app.peer_experience.providers import PeerSummaryProvider, TextEmbeddingProvider


class PeerExperienceService:
    def __init__(
        self,
        embedding_provider: TextEmbeddingProvider,
        summary_provider: PeerSummaryProvider,
        *,
        distance_threshold: float = 0.28,
        min_cluster_size: int = 3,
        provider_mode: str = "fixed-mock",
        fallback_results: dict[str, PeerExperienceDigestResult] | None = None,
    ) -> None:
        self.embedding_provider = embedding_provider
        self.summary_provider = summary_provider
        self.distance_threshold = distance_threshold
        self.min_cluster_size = min_cluster_size
        self.provider_mode = provider_mode
        self.fallback_results = fallback_results or {}

    def digest(self, request: PeerExperienceDigestRequest) -> PeerExperienceDigestResult:
        try:
            return self._digest(request)
        except SkillError:
            fallback = self.fallback_results.get(request.standard_action.action_id)
            if fallback is None:
                raise
            return fallback.model_copy(
                update={
                    "request_id": request.request_id,
                    "status": DigestStatus.DEGRADED,
                    "provider_mode": "fixed-json-fallback",
                }
            )

    def _digest(self, request: PeerExperienceDigestRequest) -> PeerExperienceDigestResult:
        unique: dict[str, MockPeerComment] = {}
        seen_text: set[str] = set()
        excluded: list[str] = []
        for comment in request.comments:
            normalized = re.sub(r"\s+", "", comment.text).lower()
            if comment.risk_type is not CommentRiskType.NORMAL or normalized in seen_text:
                excluded.append(comment.comment_id)
                continue
            seen_text.add(normalized)
            unique[comment.comment_id] = comment

        by_problem: dict[str, list[MockPeerComment]] = defaultdict(list)
        for comment in unique.values():
            by_problem[comment.problem_tag].append(comment)

        clusters: list[PeerExperienceCluster] = []
        for problem_tag, comments in sorted(by_problem.items()):
            groups = self._cluster_comments(comments, request.request_id)
            for group_index, group in enumerate(groups, start=1):
                if len(group) < self.min_cluster_size:
                    continue
                summary = self.summary_provider.summarize(
                    problem_tag,
                    group,
                    request_id=request.request_id,
                )
                comment_ids = [item.comment_id for item in group]
                clusters.append(
                    PeerExperienceCluster(
                        clusterId=f"cluster_{problem_tag.lower()}_{group_index}",
                        problemTag=problem_tag,
                        methodName=summary.method_name,
                        summary=summary.summary,
                        mentionCount=len(comment_ids),
                        sourceVideoCount=len({item.video_id for item in group}),
                        commentIds=comment_ids,
                        hasDisagreement=summary.has_disagreement,
                        riskType=CommentRiskType.NORMAL,
                    )
                )

        return PeerExperienceDigestResult(
            requestId=request.request_id,
            standardActionId=request.standard_action.action_id,
            status=DigestStatus.SUFFICIENT if clusters else DigestStatus.INSUFFICIENT,
            clusters=clusters,
            excludedCommentIds=excluded,
            providerMode=self.provider_mode,
        )

    def match(self, request: PeerExperienceMatchRequest) -> PeerExperienceMatchResult:
        if request.feedback_type is FeedbackType.DISCOMFORT:
            return PeerExperienceMatchResult(
                requestId=request.request_id,
                problemTag=None,
                matchedClusterIds=[],
                safetyRoute=True,
            )
        problem_tag = self._problem_tag(request.feedback_type, request.felt_muscles)
        matched = [
            item.cluster_id
            for item in request.available_clusters
            if item.problem_tag == problem_tag
        ]
        return PeerExperienceMatchResult(
            requestId=request.request_id,
            problemTag=problem_tag,
            matchedClusterIds=matched,
            safetyRoute=False,
        )

    def _cluster_comments(
        self,
        comments: list[MockPeerComment],
        request_id: str,
    ) -> list[list[MockPeerComment]]:
        if len(comments) <= 1:
            return [comments]
        vectors = self.embedding_provider.embed(
            [comment.text for comment in comments],
            request_id=request_id,
        )
        try:
            labels = AgglomerativeClustering(
                n_clusters=None,
                metric="cosine",
                linkage="average",
                distance_threshold=self.distance_threshold,
            ).fit_predict(vectors)
        except ValueError as exc:
            raise SkillError(
                "PEER_CLUSTERING_FAILED",
                "评论向量无法形成稳定分组。",
                request_id=request_id,
            ) from exc
        result: dict[int, list[MockPeerComment]] = defaultdict(list)
        for label, comment in zip(labels, comments, strict=True):
            result[int(label)].append(comment)
        return list(result.values())

    @staticmethod
    def _problem_tag(feedback_type: FeedbackType, felt_muscles: list[str]) -> str | None:
        if feedback_type in {FeedbackType.NO_FEELING, FeedbackType.NO_CLEAR_FEELING}:
            return "NO_TARGET_FEELING"
        if feedback_type in {FeedbackType.TOO_HARD, FeedbackType.TOO_DIFFICULT}:
            return "TOO_DIFFICULT"
        if feedback_type is FeedbackType.OTHER_FELT:
            arm_muscles = {"BICEPS", "TRICEPS", "FOREARMS"}
            return "ARMS_FELT_MORE" if arm_muscles.intersection(felt_muscles) else "OTHER_MUSCLE_FELT"
        return None
