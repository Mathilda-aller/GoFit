from pathlib import Path

from fastapi.testclient import TestClient

from app.api.routes.action_card_jobs import get_job_service
from app.jobs.action_card_jobs import ActionCardJobService
from app.main import app
from tests.test_video_workflow import make_request, make_workflow


def test_action_card_job_runs_and_can_be_queried(tmp_path: Path) -> None:
    video_path = tmp_path / "video.mp4"
    video_path.write_bytes(b"fake video")
    request = make_request(video_path)
    service = ActionCardJobService(make_workflow(tmp_path))
    app.dependency_overrides[get_job_service] = lambda: service
    client = TestClient(app)
    try:
        response = client.post(
            "/internal/v1/action-card-jobs",
            json=request.model_dump(by_alias=True, mode="json"),
        )
        assert response.status_code == 202

        fetched = client.get(
            f"/internal/v1/action-card-jobs/{request.request_id}"
        )
        assert fetched.status_code == 200
        assert fetched.json()["status"] == "COMPLETED"
        assert fetched.json()["result"]["actionCardResult"]["status"] == "READY"

        replay = client.post(
            "/internal/v1/action-card-jobs",
            json=request.model_dump(by_alias=True, mode="json"),
        )
        assert replay.headers["X-GoFit-Idempotent-Replay"] == "true"
    finally:
        app.dependency_overrides.clear()


def test_unknown_job_returns_safe_404(tmp_path: Path) -> None:
    service = ActionCardJobService(make_workflow(tmp_path))
    app.dependency_overrides[get_job_service] = lambda: service
    try:
        response = TestClient(app).get(
            "/internal/v1/action-card-jobs/not-found"
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "ACTION_CARD_JOB_NOT_FOUND"

