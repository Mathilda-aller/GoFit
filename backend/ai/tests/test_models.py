import copy

import pytest
from pydantic import ValidationError

from app.models.action_card import ActionCardBuildRequest, ActionCardBuildResult


def test_unknown_input_field_is_rejected(input_payload: dict) -> None:
    payload = copy.deepcopy(input_payload)
    payload["comments"] = ["不允许混入评论"]

    with pytest.raises(ValidationError):
        ActionCardBuildRequest.model_validate(payload)


def test_invalid_evidence_range_is_rejected(input_payload: dict) -> None:
    payload = copy.deepcopy(input_payload)
    payload["evidence"][0]["endMs"] = payload["evidence"][0]["startMs"]

    with pytest.raises(ValidationError, match="endMs must be greater than startMs"):
        ActionCardBuildRequest.model_validate(payload)


def test_output_limits_are_enforced(expected_payload: dict) -> None:
    too_many_steps = copy.deepcopy(expected_payload)
    too_many_steps["actionCard"]["learningSide"]["steps"] *= 2
    with pytest.raises(ValidationError):
        ActionCardBuildResult.model_validate(too_many_steps)

    too_many_tips = copy.deepcopy(expected_payload)
    too_many_tips["actionCard"]["trainingSide"]["quickTips"].append(
        {
            "text": "额外提示",
            "evidenceIds": ["asr_setup"],
        }
    )
    with pytest.raises(ValidationError):
        ActionCardBuildResult.model_validate(too_many_tips)


def test_learning_reminders_are_limited_to_two(expected_payload: dict) -> None:
    payload = copy.deepcopy(expected_payload)
    payload["actionCard"]["learningSide"]["keyReminders"].append(
        {
            "text": "第三条提醒",
            "evidenceIds": ["asr_setup"],
        }
    )

    with pytest.raises(ValidationError):
        ActionCardBuildResult.model_validate(payload)


def test_peer_experience_cannot_be_mixed_into_card(expected_payload: dict) -> None:
    payload = copy.deepcopy(expected_payload)
    payload["actionCard"]["peerExperience"] = {
        "summary": "来自其他视频评论区"
    }

    with pytest.raises(ValidationError):
        ActionCardBuildResult.model_validate(payload)
