import json
from pathlib import Path

import pytest

from app.models.action_card import ActionCardBuildRequest


AI_ROOT = Path(__file__).resolve().parents[1]
INPUT_PATH = AI_ROOT / "fixtures" / "lateral_raise" / "input.json"
EXPECTED_PATH = AI_ROOT / "fixtures" / "lateral_raise" / "expected-output.json"
RECOMMENDATION_INPUT_PATH = AI_ROOT / "fixtures" / "recommendation" / "input.json"
RECOMMENDATION_EXPECTED_PATH = (
    AI_ROOT / "fixtures" / "recommendation" / "expected-output.json"
)


@pytest.fixture
def input_payload() -> dict:
    return json.loads(INPUT_PATH.read_text(encoding="utf-8"))


@pytest.fixture
def expected_payload() -> dict:
    return json.loads(EXPECTED_PATH.read_text(encoding="utf-8"))


@pytest.fixture
def build_request(input_payload: dict) -> ActionCardBuildRequest:
    return ActionCardBuildRequest.model_validate(input_payload)


@pytest.fixture
def recommendation_payload() -> dict:
    return json.loads(RECOMMENDATION_INPUT_PATH.read_text(encoding="utf-8"))


@pytest.fixture
def recommendation_expected_payload() -> dict:
    return json.loads(RECOMMENDATION_EXPECTED_PATH.read_text(encoding="utf-8"))
