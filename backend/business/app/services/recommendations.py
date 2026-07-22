"""Recommendation orchestration for the business center."""

from __future__ import annotations

import json
from typing import Any

import aiosqlite
import httpx

from app.core.config import settings
from app.repositories import business as repo


def _reason_for(candidate: dict[str, Any], covered_muscles: set[str], selected_region: str | None) -> tuple[str, str]:
    primary = candidate["primary_muscles"][0] if candidate["primary_muscles"] else "目标肌群"
    if selected_region and candidate["body_region"] == selected_region and primary not in covered_muscles:
        return "MUSCLE_COVERAGE_COMPLEMENT", f"补充当前还没有覆盖的{primary}。"
    if selected_region and candidate["body_region"] == selected_region:
        return "SAME_BODY_REGION", f"同样训练{candidate['body_region']}，可以作为接下来的候选。"
    if candidate["is_saved"]:
        return "SAVED_NOT_TRIED", "你已经收藏过这张卡，可以加入练单试试。"
    return "SAME_BODY_REGION", "作为当前练单之外的候选动作。"


async def recommend_for_plan(
    db: aiosqlite.Connection,
    plan_id: str,
) -> dict[str, Any]:
    plan = await repo.get_plan(db, plan_id)
    if plan is None:
        return {
            "request_id": repo.new_id("rec"),
            "rule_version": "p0-v1-local",
            "outcome_code": "NO_SAFE_CANDIDATE",
            "items": [],
        }

    all_cards = await repo.list_action_cards(db)
    current_ids = {item["card_id"] for item in plan["items"]}
    selected_region = plan["body_regions"][0] if plan["body_regions"] else None
    current_items = [
        {
            "actionCardId": item["card_id"],
            "bodyRegion": item["card"]["body_region"],
            "primaryMuscles": item["card"]["primary_muscles"],
        }
        for item in plan["items"]
    ]
    history = await repo.fetch_all(
        db,
        """
        SELECT i.card_id AS action_card_id, i.feedback_type
        FROM training_session_items i
        JOIN training_sessions s ON s.id = i.session_id
        WHERE s.user_id = ? AND i.feedback_type IS NOT NULL
        """,
        (repo.DEMO_USER_ID,),
    )
    excluded_ids = [
        row["action_card_id"]
        for row in history
        if row["feedback_type"] == "DISCOMFORT"
    ]
    candidates = [
        {
            "actionCardId": card["id"],
            "bodyRegion": card["body_region"],
            "primaryMuscles": card["primary_muscles"],
            "secondaryMuscles": card["secondary_muscles"],
            "isSaved": card["is_saved"],
            "hasTried": any(row["action_card_id"] == card["id"] for row in history),
            "contentReady": card["status"] == "READY",
            "sourceRisk": False,
        }
        for card in all_cards
    ]
    request_id = repo.new_id("rec")
    payload = {
        "requestId": request_id,
        "selectedBodyRegion": selected_region,
        "currentItems": current_items,
        "candidates": candidates,
        "history": [
            {"actionCardId": row["action_card_id"], "feedbackType": row["feedback_type"]}
            for row in history
        ],
        "excludedActionCardIds": excluded_ids,
    }
    result = await _rank_with_ai(payload)
    if result is None:
        result = _rank_locally(request_id, all_cards, current_ids, excluded_ids, selected_region, plan)

    cards_by_id = {card["id"]: card for card in all_cards}
    items = []
    for item in result["items"]:
        card = cards_by_id.get(item["actionCardId"])
        if card is not None:
            items.append(
                {
                    "card": card,
                    "reason_code": item["reasonCode"],
                    "reason_text": item["reasonText"],
                }
            )
    response = {
        "request_id": result["requestId"],
        "rule_version": result["ruleVersion"],
        "outcome_code": result["outcomeCode"],
        "items": items,
    }
    await db.execute(
        """
        INSERT INTO recommendation_events (id, user_id, plan_id, request_data, result_data)
        VALUES (?, ?, ?, ?, ?)
        """,
        (
            request_id,
            repo.DEMO_USER_ID,
            plan_id,
            json.dumps(payload, ensure_ascii=False),
            json.dumps(response, ensure_ascii=False),
        ),
    )
    await db.commit()
    return response


async def _rank_with_ai(payload: dict[str, Any]) -> dict[str, Any] | None:
    try:
        async with httpx.AsyncClient(timeout=1.5) as client:
            response = await client.post(
                f"{settings.ai_center_url}/internal/v1/recommendations/rank",
                json=payload,
            )
        response.raise_for_status()
        return response.json()
    except httpx.HTTPError:
        return None


def _rank_locally(
    request_id: str,
    cards: list[dict[str, Any]],
    current_ids: set[str],
    excluded_ids: list[str],
    selected_region: str | None,
    plan: dict[str, Any],
) -> dict[str, Any]:
    covered = {
        muscle
        for item in plan["items"]
        for muscle in item["card"]["primary_muscles"]
    }
    usable = [
        card
        for card in cards
        if card["id"] not in current_ids
        and card["id"] not in excluded_ids
        and card["status"] == "READY"
    ]
    usable.sort(
        key=lambda card: (
            card["body_region"] != selected_region,
            bool(set(card["primary_muscles"]) & covered),
            card["id"],
        )
    )
    items = []
    for card in usable[:3]:
        reason_code, reason_text = _reason_for(card, covered, selected_region)
        items.append(
            {
                "actionCardId": card["id"],
                "reasonCode": reason_code,
                "reasonText": reason_text,
            }
        )
    return {
        "requestId": request_id,
        "ruleVersion": "p0-v1-local",
        "outcomeCode": "OK" if items else "NO_SAFE_CANDIDATE",
        "items": items,
    }
