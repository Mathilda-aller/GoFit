from __future__ import annotations

import json
from pathlib import Path

from pydantic import ValidationError

from app.errors import SkillError
from app.models.action_card import ActionCardBuildRequest, ActionCardBuildResult


class FixedFixtureActionCardGenerator:
    """Deterministic provider for the single lateral-raise demo fixture."""

    supported_video_id = "video_lateral_raise_demo"

    def __init__(self, fixture_path: Path | None = None) -> None:
        self.fixture_path = fixture_path or (
            Path(__file__).resolve().parents[2]
            / "fixtures"
            / "lateral_raise"
            / "expected-output.json"
        )

    def generate(self, request: ActionCardBuildRequest) -> ActionCardBuildResult:
        candidate_ids = {
            candidate.standard_action_id
            for candidate in request.standard_action_candidates
        }
        if (
            request.source_video.video_id != self.supported_video_id
            or "action_lateral_raise" not in candidate_ids
        ):
            raise SkillError(
                "MOCK_FIXTURE_NOT_FOUND",
                "固定假模型只支持 video_lateral_raise_demo 场景。",
                request_id=request.request_id,
            )

        try:
            payload = json.loads(self.fixture_path.read_text(encoding="utf-8"))
            payload["requestId"] = request.request_id
            return ActionCardBuildResult.model_validate(payload)
        except (OSError, json.JSONDecodeError, ValidationError) as exc:
            raise SkillError(
                "OUTPUT_VALIDATION_FAILED",
                "固定假模型的输出不符合动作卡契约。",
                request_id=request.request_id,
            ) from exc

