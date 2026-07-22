import copy

import pytest

from app.errors import SkillError
from app.models.action_card import ActionCardBuildRequest, ActionCardBuildResult
from app.providers.fake import FixedFixtureActionCardGenerator
from app.skills.fitness_video_to_action_card import FitnessVideoToActionCardSkill


class StaticGenerator:
    def __init__(self, result: ActionCardBuildResult) -> None:
        self.result = result

    def generate(self, _request: ActionCardBuildRequest) -> ActionCardBuildResult:
        return self.result


def test_fixed_fixture_matches_expected(
    build_request: ActionCardBuildRequest,
    expected_payload: dict,
) -> None:
    result = FitnessVideoToActionCardSkill(
        FixedFixtureActionCardGenerator()
    ).execute(build_request)

    assert result.model_dump(by_alias=True, mode="json") == expected_payload


def test_unknown_video_does_not_receive_fixture(input_payload: dict) -> None:
    payload = copy.deepcopy(input_payload)
    payload["sourceVideo"]["videoId"] = "unknown_video"
    request = ActionCardBuildRequest.model_validate(payload)

    with pytest.raises(SkillError) as caught:
        FitnessVideoToActionCardSkill(
            FixedFixtureActionCardGenerator()
        ).execute(request)

    assert caught.value.code == "MOCK_FIXTURE_NOT_FOUND"


def test_unknown_evidence_reference_is_rejected(
    build_request: ActionCardBuildRequest,
    expected_payload: dict,
) -> None:
    payload = copy.deepcopy(expected_payload)
    payload["actionCard"]["trainingSide"]["quickCue"]["evidenceIds"] = [
        "missing_evidence"
    ]
    result = ActionCardBuildResult.model_validate(payload)

    with pytest.raises(SkillError) as caught:
        FitnessVideoToActionCardSkill(StaticGenerator(result)).execute(build_request)

    assert caught.value.code == "UNKNOWN_EVIDENCE_REFERENCE"


def test_unknown_media_candidate_evidence_is_rejected(input_payload: dict) -> None:
    payload = copy.deepcopy(input_payload)
    payload["mediaCandidates"][0]["evidenceIds"] = ["missing_evidence"]
    request = ActionCardBuildRequest.model_validate(payload)

    with pytest.raises(SkillError) as caught:
        FitnessVideoToActionCardSkill(
            FixedFixtureActionCardGenerator()
        ).execute(request)

    assert caught.value.code == "UNKNOWN_EVIDENCE_REFERENCE"


def test_common_errors_need_explicit_error_demo_evidence(
    input_payload: dict,
    expected_payload: dict,
) -> None:
    request_payload = copy.deepcopy(input_payload)
    request_payload["mediaCandidates"] = [
        item
        for item in request_payload["mediaCandidates"]
        if item["kind"] != "ERROR_DEMO"
    ]
    request = ActionCardBuildRequest.model_validate(request_payload)

    bad_output = copy.deepcopy(expected_payload)
    result = ActionCardBuildResult.model_validate(bad_output)

    with pytest.raises(SkillError) as caught:
        FitnessVideoToActionCardSkill(StaticGenerator(result)).execute(request)
    assert caught.value.code == "OUTPUT_VALIDATION_FAILED"

    good_output = copy.deepcopy(bad_output)
    good_output["actionCard"]["learningSide"]["commonErrors"] = []
    valid_result = ActionCardBuildResult.model_validate(good_output)
    assert (
        FitnessVideoToActionCardSkill(StaticGenerator(valid_result))
        .execute(request)
        .action_card.learning_side.common_errors
        == []
    )


def test_front_and_back_must_use_the_same_demo(
    build_request: ActionCardBuildRequest,
    expected_payload: dict,
) -> None:
    payload = copy.deepcopy(expected_payload)
    payload["actionCard"]["trainingSide"]["loopDemo"] = {
        "kind": "POSTER",
        "candidateId": "poster_raise",
        "startMs": 10000,
        "endMs": 11000,
        "evidenceIds": ["vision_raise"],
    }
    result = ActionCardBuildResult.model_validate(payload)

    with pytest.raises(SkillError) as caught:
        FitnessVideoToActionCardSkill(StaticGenerator(result)).execute(build_request)

    assert caught.value.code == "OUTPUT_VALIDATION_FAILED"
