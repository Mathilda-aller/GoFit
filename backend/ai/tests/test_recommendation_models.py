import copy

import pytest
from pydantic import ValidationError

from app.models.recommendation import (
    RecommendationRankRequest,
    RecommendationRankResult,
)


def test_request_accepts_empty_context_and_optional_region() -> None:
    request = RecommendationRankRequest.model_validate({"requestId": "rec_empty"})

    assert request.selected_body_region is None
    assert request.current_items == []
    assert request.candidates == []
    assert request.history == []


def test_unknown_top_level_field_is_rejected(recommendation_payload: dict) -> None:
    payload = copy.deepcopy(recommendation_payload)
    payload["userPrivateNote"] = "must not be accepted"

    with pytest.raises(ValidationError):
        RecommendationRankRequest.model_validate(payload)


def test_unknown_feedback_type_is_rejected(recommendation_payload: dict) -> None:
    payload = copy.deepcopy(recommendation_payload)
    payload["history"][0]["feedbackType"] = "UNKNOWN_FEEDBACK"

    with pytest.raises(ValidationError):
        RecommendationRankRequest.model_validate(payload)


def test_response_enforces_limit_and_never_defines_score(
    recommendation_expected_payload: dict,
) -> None:
    result = RecommendationRankResult.model_validate(recommendation_expected_payload)
    assert "score" not in result.model_dump_json()

    payload = copy.deepcopy(recommendation_expected_payload)
    payload["items"].append(copy.deepcopy(payload["items"][0]))
    with pytest.raises(ValidationError):
        RecommendationRankResult.model_validate(payload)
