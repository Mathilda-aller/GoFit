import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.peer_experience.config import get_peer_experience_settings
from app.errors import SkillError
from app.models.peer_experience import PeerExperienceDigestRequest, PeerExperienceDigestResult
from app.peer_experience.providers import FixedMockPeerProvider
from app.peer_experience.service import PeerExperienceService


FIXTURE_DIR = Path(__file__).resolve().parents[1] / "fixtures" / "peer_experience"


@pytest.fixture(autouse=True)
def use_fixed_provider_for_contract_tests(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("GOFIT_PEER_PROVIDER", "fixed-mock")
    get_peer_experience_settings.cache_clear()
    yield
    get_peer_experience_settings.cache_clear()


def _fixture(name: str) -> dict:
    return json.loads((FIXTURE_DIR / name).read_text(encoding="utf-8"))


def test_digest_clusters_mock_comments_and_excludes_risk() -> None:
    response = TestClient(app).post(
        "/internal/v1/peer-experiences/digest",
        json=_fixture("digest-input.json"),
    )
    assert response.status_code == 200
    assert response.json() == _fixture("expected-digest.json")


def test_match_maps_other_felt_to_existing_arm_clusters() -> None:
    response = TestClient(app).post(
        "/internal/v1/peer-experiences/match",
        json=_fixture("match-input.json"),
    )
    assert response.status_code == 200
    assert response.json() == {
        "requestId": "peer_match_demo_001",
        "problemTag": "ARMS_FELT_MORE",
        "matchedClusterIds": [
            "cluster_arms_felt_more_1",
            "cluster_arms_felt_more_2",
        ],
        "safetyRoute": False,
    }


def test_discomfort_goes_directly_to_safety_route() -> None:
    payload = _fixture("match-input.json")
    payload["feedbackType"] = "DISCOMFORT"
    response = TestClient(app).post(
        "/internal/v1/peer-experiences/match",
        json=payload,
    )
    assert response.status_code == 200
    assert response.json()["safetyRoute"] is True
    assert response.json()["matchedClusterIds"] == []
    assert response.json()["problemTag"] is None


def test_model_failure_uses_checked_fixed_json() -> None:
    class BrokenProvider(FixedMockPeerProvider):
        def embed(self, texts, *, request_id):
            raise SkillError("PEER_MODEL_API_FAILED", "offline", request_id=request_id)

    fallback = PeerExperienceDigestResult.model_validate(_fixture("expected-digest.json"))
    service = PeerExperienceService(
        BrokenProvider(),
        BrokenProvider(),
        provider_mode="aliyun-live",
        fallback_results={fallback.standard_action_id: fallback},
    )
    request = PeerExperienceDigestRequest.model_validate(_fixture("digest-input.json"))
    result = service.digest(request)
    assert result.status.value == "DEGRADED"
    assert result.provider_mode == "fixed-json-fallback"
    assert len(result.clusters) == 2


def test_invalid_digest_contract_has_peer_error() -> None:
    response = TestClient(app).post(
        "/internal/v1/peer-experiences/digest",
        json={"requestId": "peer_invalid", "comments": []},
    )
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "INVALID_PEER_EXPERIENCE_REQUEST"
