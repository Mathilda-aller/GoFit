from __future__ import annotations

from typing import Any

from pydantic import ValidationError


class SkillError(Exception):
    """An expected, safe-to-return error from an AI skill."""

    def __init__(
        self,
        code: str,
        message: str,
        *,
        request_id: str | None = None,
        retryable: bool = False,
    ) -> None:
        super().__init__(message)
        self.code = code
        self.message = message
        self.request_id = request_id
        self.retryable = retryable

    def as_response(self) -> dict[str, Any]:
        return {
            "error": {
                "code": self.code,
                "message": self.message,
                "retryable": self.retryable,
                "requestId": self.request_id,
            }
        }


def request_id_from_body(body: Any) -> str | None:
    if isinstance(body, dict):
        value = body.get("requestId")
        return value if isinstance(value, str) else None
    return None


def contract_validation_error(
    error: ValidationError,
    *,
    request_id: str | None = None,
) -> SkillError:
    errors = error.errors()
    locations = [tuple(str(part) for part in item.get("loc", ())) for item in errors]
    messages = [str(item.get("msg", "")) for item in errors]

    if any("endMs must be greater than startMs" in message for message in messages):
        return SkillError(
            "INVALID_EVIDENCE_RANGE",
            "证据或媒体候选的结束时间必须晚于开始时间。",
            request_id=request_id,
        )

    if any(location[-1:] == ("evidence",) for location in locations):
        return SkillError(
            "NO_EVIDENCE",
            "缺少生成动作卡所需的来源证据。",
            request_id=request_id,
        )

    if any("standardActionCandidates" in location for location in locations):
        return SkillError(
            "NO_STANDARD_ACTION_CANDIDATES",
            "缺少业务后端提供的标准动作候选。",
            request_id=request_id,
        )

    return SkillError(
        "OUTPUT_VALIDATION_FAILED",
        "请求或输出不符合动作卡契约。",
        request_id=request_id,
    )
