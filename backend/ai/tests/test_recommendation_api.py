from fastapi.testclient import TestClient

from app.api.routes.recommendations import get_ranker
from app.main import app


def test_recommendation_endpoint_matches_fixture(
    recommendation_payload: dict,
    recommendation_expected_payload: dict,
) -> None:
    response = TestClient(app).post(
        "/internal/v1/recommendations/rank",
        json=recommendation_payload,
    )
    assert response.status_code == 200
    assert response.json() == recommendation_expected_payload


def test_empty_candidates_return_normal_empty_outcome() -> None:
    response = TestClient(app).post(
        "/internal/v1/recommendations/rank",
        json={"requestId": "rec_empty", "candidates": []},
    )
    assert response.status_code == 200
    assert response.json() == {
        "requestId": "rec_empty",
        "ruleVersion": "p0-v1",
        "outcomeCode": "NO_SAFE_CANDIDATE",
        "items": [],
    }


def test_invalid_request_has_recommendation_error() -> None:
    response = TestClient(app).post(
        "/internal/v1/recommendations/rank",
        json={"requestId": "", "history": [{"feedbackType": "UNKNOWN"}]},
    )
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "INVALID_RECOMMENDATION_REQUEST"
    assert "动作卡" not in response.json()["error"]["message"]


def test_unexpected_recommendation_error_is_not_exposed(
    recommendation_payload: dict,
) -> None:
    class BrokenRanker:
        def rank(self, _request):
            raise RuntimeError("secret recommendation detail")

    app.dependency_overrides[get_ranker] = lambda: BrokenRanker()
    try:
        response = TestClient(app, raise_server_exceptions=False).post(
            "/internal/v1/recommendations/rank",
            json=recommendation_payload,
            headers={"X-Request-Id": "rec_demo_001"},
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 500
    assert "secret" not in response.text
    assert response.json()["error"] == {
        "code": "RECOMMENDATION_FAILED",
        "message": "动作推荐失败，请继续手动选择动作。",
        "retryable": False,
        "requestId": "rec_demo_001",
    }
