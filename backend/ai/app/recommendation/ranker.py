from __future__ import annotations

import logging
from collections import Counter, defaultdict
from dataclasses import dataclass

from app.models.recommendation import (
    FeedbackType,
    RecommendationCandidate,
    RecommendationHistoryItem,
    RecommendationItem,
    RecommendationOutcomeCode,
    RecommendationRankRequest,
    RecommendationRankResult,
    RecommendationReasonCode,
)
from app.recommendation import config


logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class _RankedCandidate:
    action_card_id: str
    score: int
    is_saved: bool
    has_tried: bool
    completeness: int
    reason_code: RecommendationReasonCode
    reason_text: str


class RecommendationRanker:
    """Deterministic P0 rules for ranking action-card candidates."""

    def rank(self, request: RecommendationRankRequest) -> RecommendationRankResult:
        current_ids = {item.action_card_id for item in request.current_items}
        excluded_ids = set(request.excluded_action_card_ids)
        discomfort_ids = {
            item.action_card_id
            for item in request.history
            if item.feedback_type == FeedbackType.DISCOMFORT
        }
        current_muscles = {
            muscle
            for item in request.current_items
            for muscle in item.primary_muscles
            if muscle
        }
        current_muscle_sets = {
            frozenset(muscle for muscle in item.primary_muscles if muscle)
            for item in request.current_items
        }
        primary_body_region = self._primary_body_region(request)
        history = self._history_by_card(request.history)
        seen_ids: set[str] = set()
        ranked: list[_RankedCandidate] = []

        for candidate in request.candidates:
            candidate_id = self._valid_candidate_id(candidate)
            skip_reason = self._hard_filter_reason(
                candidate,
                candidate_id,
                current_ids=current_ids,
                excluded_ids=excluded_ids,
                discomfort_ids=discomfort_ids,
            )
            if skip_reason is not None:
                self._log_skip(request.request_id, candidate_id, skip_reason)
                continue
            assert candidate_id is not None

            if candidate_id in seen_ids:
                self._log_skip(request.request_id, candidate_id, "DUPLICATE_CANDIDATE")
                continue
            seen_ids.add(candidate_id)

            candidate_history = history[candidate_id]
            score = self._score(
                candidate,
                candidate_history,
                selected_body_region=request.selected_body_region,
                primary_body_region=primary_body_region,
                current_muscles=current_muscles,
                current_muscle_sets=current_muscle_sets,
            )
            reason = self._reason(
                candidate,
                candidate_history,
                selected_body_region=request.selected_body_region,
                primary_body_region=primary_body_region,
                current_muscles=current_muscles,
            )
            if reason is None:
                self._log_skip(request.request_id, candidate_id, "NO_EXPLAINABLE_REASON")
                continue

            reason_code, reason_text = reason
            ranked.append(
                _RankedCandidate(
                    action_card_id=candidate_id,
                    score=score,
                    is_saved=candidate.is_saved is True,
                    has_tried=candidate.has_tried is True,
                    completeness=self._completeness(candidate),
                    reason_code=reason_code,
                    reason_text=reason_text,
                )
            )

        ranked.sort(
            key=lambda item: (
                -item.score,
                -int(item.is_saved),
                int(item.has_tried),
                -item.completeness,
                item.action_card_id,
            )
        )
        selected = ranked[: config.MAX_RECOMMENDATIONS]
        outcome = (
            RecommendationOutcomeCode.OK
            if selected
            else RecommendationOutcomeCode.NO_SAFE_CANDIDATE
        )
        return RecommendationRankResult(
            requestId=request.request_id,
            ruleVersion=config.RULE_VERSION,
            outcomeCode=outcome,
            items=[
                RecommendationItem(
                    actionCardId=item.action_card_id,
                    reasonCode=item.reason_code,
                    reasonText=item.reason_text,
                )
                for item in selected
            ],
        )

    @staticmethod
    def _primary_body_region(request: RecommendationRankRequest) -> str | None:
        counts = Counter(
            item.body_region
            for item in request.current_items
            if item.body_region is not None
        )
        if not counts:
            return None
        return min(counts, key=lambda region: (-counts[region], region))

    @staticmethod
    def _history_by_card(
        history: list[RecommendationHistoryItem],
    ) -> defaultdict[str, Counter[str]]:
        grouped: defaultdict[str, Counter[str]] = defaultdict(Counter)
        for item in history:
            feedback = item.feedback_type
            if feedback in {FeedbackType.NO_FEELING, FeedbackType.NO_CLEAR_FEELING}:
                normalized = "NO_FEELING"
            elif feedback in {FeedbackType.TOO_HARD, FeedbackType.TOO_DIFFICULT}:
                normalized = "TOO_HARD"
            else:
                normalized = feedback.value
            grouped[item.action_card_id][normalized] += 1
        return grouped

    @staticmethod
    def _valid_candidate_id(candidate: RecommendationCandidate) -> str | None:
        candidate_id = candidate.action_card_id
        if candidate_id is None or not candidate_id.strip():
            return None
        return candidate_id.strip()

    @staticmethod
    def _hard_filter_reason(
        candidate: RecommendationCandidate,
        candidate_id: str | None,
        *,
        current_ids: set[str],
        excluded_ids: set[str],
        discomfort_ids: set[str],
    ) -> str | None:
        if candidate_id is None:
            return "MISSING_ACTION_CARD_ID"
        if candidate_id in current_ids:
            return "ALREADY_IN_CURRENT_WORKOUT"
        if candidate_id in discomfort_ids:
            return "HISTORY_DISCOMFORT"
        if candidate_id in excluded_ids:
            return "EXCLUDED_BY_PREFERENCE"
        if candidate.content_ready is not True:
            return "CONTENT_NOT_READY"
        if candidate.source_risk is not False:
            return "SOURCE_RISK_UNRESOLVED"
        if candidate.body_region is None or not candidate.body_region.strip():
            return "MISSING_BODY_REGION"
        primary_muscles = candidate.primary_muscles
        if not primary_muscles or not any(muscle.strip() for muscle in primary_muscles):
            return "MISSING_PRIMARY_MUSCLES"
        return None

    @staticmethod
    def _score(
        candidate: RecommendationCandidate,
        history: Counter[str],
        *,
        selected_body_region: str | None,
        primary_body_region: str | None,
        current_muscles: set[str],
        current_muscle_sets: set[frozenset[str]],
    ) -> int:
        assert candidate.body_region is not None
        assert candidate.primary_muscles is not None
        candidate_muscles = frozenset(
            muscle for muscle in candidate.primary_muscles if muscle
        )
        score = 0
        if selected_body_region and candidate.body_region == selected_body_region:
            score += config.SCORE_SELECTED_BODY_REGION
        if primary_body_region and candidate.body_region == primary_body_region:
            score += config.SCORE_CURRENT_BODY_REGION
        if current_muscles and candidate_muscles - current_muscles:
            score += config.SCORE_MUSCLE_COVERAGE_COMPLEMENT
        score += min(
            history[FeedbackType.TARGET_FELT.value] * config.SCORE_HISTORY_TARGET_FELT,
            config.MAX_HISTORY_TARGET_FELT,
        )
        if candidate.is_saved is True and candidate.has_tried is not True:
            score += config.SCORE_SAVED_NOT_TRIED
        if candidate_muscles in current_muscle_sets:
            score += config.SCORE_HIGHLY_REPETITIVE
        score += max(
            history["NO_FEELING"] * config.SCORE_NO_FEELING,
            config.MIN_NO_FEELING,
        )
        score += max(
            history["TOO_HARD"] * config.SCORE_TOO_HARD,
            config.MIN_TOO_HARD,
        )
        return score

    @staticmethod
    def _reason(
        candidate: RecommendationCandidate,
        history: Counter[str],
        *,
        selected_body_region: str | None,
        primary_body_region: str | None,
        current_muscles: set[str],
    ) -> tuple[RecommendationReasonCode, str] | None:
        assert candidate.body_region is not None
        assert candidate.primary_muscles is not None
        candidate_muscles = {muscle for muscle in candidate.primary_muscles if muscle}
        if history[FeedbackType.TARGET_FELT.value] > 0:
            return (
                RecommendationReasonCode.HISTORY_TARGET_FELT,
                config.REASON_TEMPLATES["HISTORY_TARGET_FELT"],
            )

        complementary = sorted(candidate_muscles - current_muscles)
        if current_muscles and complementary:
            muscle_label = config.MUSCLE_LABELS.get(complementary[0])
            template_key = (
                "MUSCLE_COVERAGE_COMPLEMENT"
                if muscle_label
                else "MUSCLE_COVERAGE_COMPLEMENT_GENERIC"
            )
            return (
                RecommendationReasonCode.MUSCLE_COVERAGE_COMPLEMENT,
                config.REASON_TEMPLATES[template_key].format(
                    muscle_label=muscle_label or ""
                ),
            )

        same_region = (
            selected_body_region is not None
            and candidate.body_region == selected_body_region
        ) or (
            primary_body_region is not None
            and candidate.body_region == primary_body_region
        )
        if same_region:
            body_region_label = config.BODY_REGION_LABELS.get(candidate.body_region)
            template_key = (
                "SAME_BODY_REGION"
                if body_region_label
                else "SAME_BODY_REGION_GENERIC"
            )
            return (
                RecommendationReasonCode.SAME_BODY_REGION,
                config.REASON_TEMPLATES[template_key].format(
                    body_region_label=body_region_label or ""
                ),
            )

        if candidate.is_saved is True and candidate.has_tried is not True:
            return (
                RecommendationReasonCode.SAVED_NOT_TRIED,
                config.REASON_TEMPLATES["SAVED_NOT_TRIED"],
            )
        return None

    @staticmethod
    def _completeness(candidate: RecommendationCandidate) -> int:
        return sum(
            (
                bool(candidate.body_region),
                bool(candidate.primary_muscles),
                bool(candidate.secondary_muscles),
                candidate.is_saved is not None,
                candidate.has_tried is not None,
                candidate.content_ready is not None,
                candidate.source_risk is not None,
            )
        )

    @staticmethod
    def _log_skip(request_id: str, candidate_id: str | None, reason: str) -> None:
        logger.info(
            "recommendation_candidate_skipped request_id=%s action_card_id=%s reason=%s",
            request_id,
            candidate_id or "<missing>",
            reason,
        )
