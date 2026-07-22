"""Training feedback business rules."""

from __future__ import annotations


def problem_tag_for_feedback(feedback_type: str, felt_muscles: list[str]) -> str | None:
    if feedback_type in {"NO_FEELING", "NO_CLEAR_FEELING"}:
        return "NO_TARGET_FEELING"
    if feedback_type in {"TOO_HARD", "TOO_DIFFICULT"}:
        return "TOO_DIFFICULT"
    if feedback_type == "OTHER_FELT":
        joined = " ".join(felt_muscles).lower()
        if "手臂" in joined or "肱二头" in joined or "肱三头" in joined:
            return "ARMS_FELT_MORE"
        if "arm" in joined or "biceps" in joined or "triceps" in joined:
            return "ARMS_FELT_MORE"
        return "OTHER_MUSCLE_FELT_MORE"
    if feedback_type == "DISCOMFORT":
        return "DISCOMFORT"
    return None


def is_safety_feedback(feedback_type: str) -> bool:
    return feedback_type == "DISCOMFORT"
