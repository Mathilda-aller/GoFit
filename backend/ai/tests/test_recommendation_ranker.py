import copy
from collections import Counter

from app.models.recommendation import RecommendationCandidate, RecommendationRankRequest
from app.recommendation.ranker import RecommendationRanker


def _rank(payload: dict):
    return RecommendationRanker().rank(RecommendationRankRequest.model_validate(payload))


def _candidate(card_id: str, **overrides) -> dict:
    candidate = {
        "actionCardId": card_id,
        "bodyRegion": "SHOULDER",
        "primaryMuscles": ["DELTOID_LATERAL"],
        "secondaryMuscles": [],
        "isSaved": False,
        "hasTried": True,
        "contentReady": True,
        "sourceRisk": False,
    }
    candidate.update(overrides)
    return candidate


def test_fixture_ranking_is_exact(
    recommendation_payload: dict,
    recommendation_expected_payload: dict,
) -> None:
    result = _rank(recommendation_payload)
    assert result.model_dump(by_alias=True, mode="json") == recommendation_expected_payload


def test_hard_filters_and_duplicate_candidate_are_removed() -> None:
    payload = {
        "requestId": "rec_filters",
        "selectedBodyRegion": "SHOULDER",
        "currentItems": [
            {
                "actionCardId": "current",
                "bodyRegion": "SHOULDER",
                "primaryMuscles": ["DELTOID_ANTERIOR"],
            }
        ],
        "candidates": [
            _candidate("current"),
            _candidate("excluded"),
            _candidate("discomfort"),
            _candidate("risky", sourceRisk=True),
            _candidate("not_ready", contentReady=False),
            _candidate("missing_region", bodyRegion=None),
            _candidate("missing_muscle", primaryMuscles=[]),
            _candidate("valid"),
            _candidate("valid", primaryMuscles=["DELTOID_POSTERIOR"]),
        ],
        "history": [
            {"actionCardId": "discomfort", "feedbackType": "DISCOMFORT"}
        ],
        "excludedActionCardIds": ["excluded"],
    }

    result = _rank(payload)
    assert [item.action_card_id for item in result.items] == ["valid"]


def test_weight_caps_and_feedback_aliases_are_applied() -> None:
    candidate = RecommendationCandidate.model_validate(_candidate("candidate"))
    score = RecommendationRanker._score(
        candidate,
        Counter({"TARGET_FELT": 9, "NO_FEELING": 9, "TOO_HARD": 9}),
        selected_body_region="SHOULDER",
        primary_body_region="SHOULDER",
        current_muscles={"DELTOID_ANTERIOR"},
        current_muscle_sets={frozenset({"DELTOID_LATERAL"})},
    )
    # +30 +20 +18 +24 -20 -24 -18
    assert score == 30

    alias_payload = {
        "requestId": "rec_aliases",
        "selectedBodyRegion": "SHOULDER",
        "candidates": [_candidate("a"), _candidate("b")],
        "history": [
            {"actionCardId": "a", "feedbackType": "NO_FEELING"},
            {"actionCardId": "a", "feedbackType": "TOO_HARD"},
            {"actionCardId": "b", "feedbackType": "NO_CLEAR_FEELING"},
            {"actionCardId": "b", "feedbackType": "TOO_DIFFICULT"},
        ],
    }
    assert [item.action_card_id for item in _rank(alias_payload).items] == ["a", "b"]


def test_reason_priority_prefers_history_over_coverage_and_saved() -> None:
    payload = {
        "requestId": "rec_reason",
        "selectedBodyRegion": "SHOULDER",
        "currentItems": [
            {
                "actionCardId": "current",
                "bodyRegion": "SHOULDER",
                "primaryMuscles": ["DELTOID_ANTERIOR"],
            }
        ],
        "candidates": [_candidate("candidate", isSaved=True, hasTried=False)],
        "history": [
            {"actionCardId": "candidate", "feedbackType": "TARGET_FELT"}
        ],
    }

    assert _rank(payload).items[0].reason_code == "HISTORY_TARGET_FELT"


def test_primary_region_tie_uses_lexical_region_code() -> None:
    payload = {
        "requestId": "rec_region_tie",
        "currentItems": [
            {"actionCardId": "one", "bodyRegion": "BACK", "primaryMuscles": ["LAT"]},
            {"actionCardId": "two", "bodyRegion": "ARM", "primaryMuscles": ["BICEPS"]},
        ],
        "candidates": [
            _candidate("back", bodyRegion="BACK", primaryMuscles=["LAT"], isSaved=True, hasTried=False),
            _candidate("arm", bodyRegion="ARM", primaryMuscles=["BICEPS"], isSaved=True, hasTried=False),
        ],
    }

    assert [item.action_card_id for item in _rank(payload).items] == ["arm", "back"]


def test_unique_candidate_order_does_not_change_result(recommendation_payload: dict) -> None:
    original = _rank(recommendation_payload)
    reversed_payload = copy.deepcopy(recommendation_payload)
    reversed_payload["candidates"].reverse()
    reordered = _rank(reversed_payload)

    assert original == reordered


def test_no_explainable_or_safe_candidate_returns_empty_outcome() -> None:
    payload = {
        "requestId": "rec_empty",
        "candidates": [
            _candidate("no_signal", bodyRegion="UNKNOWN", primaryMuscles=["UNKNOWN"]),
            _candidate("unsafe", sourceRisk=True),
        ],
    }

    result = _rank(payload)
    assert result.outcome_code == "NO_SAFE_CANDIDATE"
    assert result.items == []
