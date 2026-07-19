import copy

from fastapi.testclient import TestClient

from app.api.routes.action_cards import get_skill
from app.main import app


def test_health_endpoint() -> None:
    response = TestClient(app).get("/internal/v1/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_build_endpoint_matches_fixture(
    input_payload: dict,
    expected_payload: dict,
) -> None:
    response = TestClient(app).post(
        "/internal/v1/action-cards/build",
        json=input_payload,
    )
    assert response.status_code == 200
    assert response.json() == expected_payload


def test_missing_evidence_has_stable_error(input_payload: dict) -> None:
    payload = copy.deepcopy(input_payload)
    payload["evidence"] = []
    response = TestClient(app).post(
        "/internal/v1/action-cards/build",
        json=payload,
    )
    assert response.status_code == 422
    assert response.json() == {
        "error": {
            "code": "NO_EVIDENCE",
            "message": "缺少生成动作卡所需的来源证据。",
            "retryable": False,
            "requestId": "demo_action_card_001",
        }
    }


def test_missing_candidates_has_stable_error(input_payload: dict) -> None:
    payload = copy.deepcopy(input_payload)
    payload["standardActionCandidates"] = []
    response = TestClient(app).post(
        "/internal/v1/action-cards/build",
        json=payload,
    )
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "NO_STANDARD_ACTION_CANDIDATES"


def test_invalid_range_has_stable_error(input_payload: dict) -> None:
    payload = copy.deepcopy(input_payload)
    payload["evidence"][0]["endMs"] = payload["evidence"][0]["startMs"]
    response = TestClient(app).post(
        "/internal/v1/action-cards/build",
        json=payload,
    )
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "INVALID_EVIDENCE_RANGE"


def test_unknown_video_returns_fixture_error(input_payload: dict) -> None:
    payload = copy.deepcopy(input_payload)
    payload["sourceVideo"]["videoId"] = "unknown_video"
    response = TestClient(app).post(
        "/internal/v1/action-cards/build",
        json=payload,
    )
    assert response.status_code == 404
    assert response.json()["error"]["code"] == "MOCK_FIXTURE_NOT_FOUND"


def test_unexpected_exception_is_not_exposed(input_payload: dict) -> None:
    class BrokenSkill:
        def execute(self, _request):
            raise RuntimeError("secret internal detail")

    app.dependency_overrides[get_skill] = lambda: BrokenSkill()
    try:
        response = TestClient(app, raise_server_exceptions=False).post(
            "/internal/v1/action-cards/build",
            json=input_payload,
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 500
    assert "secret" not in response.text
    assert response.json()["error"]["code"] == "OUTPUT_VALIDATION_FAILED"

