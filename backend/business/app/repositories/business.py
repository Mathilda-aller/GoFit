"""Repository helpers for the MVP business API."""

from __future__ import annotations

import json
import uuid
from typing import Any

import aiosqlite

DEMO_USER_ID = "demo_user_001"


def new_id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:12]}"


def json_list(value: str | None) -> list[str]:
    if not value:
        return []
    parsed = json.loads(value)
    return parsed if isinstance(parsed, list) else []


def row_dict(row: aiosqlite.Row | None) -> dict[str, Any] | None:
    return dict(row) if row is not None else None


async def fetch_one(
    db: aiosqlite.Connection,
    sql: str,
    params: tuple[Any, ...] = (),
) -> dict[str, Any] | None:
    cursor = await db.execute(sql, params)
    row = await cursor.fetchone()
    return row_dict(row)


async def fetch_all(
    db: aiosqlite.Connection,
    sql: str,
    params: tuple[Any, ...] = (),
) -> list[dict[str, Any]]:
    cursor = await db.execute(sql, params)
    rows = await cursor.fetchall()
    return [dict(row) for row in rows]


async def get_source_video(db: aiosqlite.Connection, video_id: str) -> dict[str, Any] | None:
    return await fetch_one(db, "SELECT * FROM source_videos WHERE id = ?", (video_id,))


async def get_action_card(
    db: aiosqlite.Connection,
    card_id: str,
    user_id: str = DEMO_USER_ID,
) -> dict[str, Any] | None:
    row = await fetch_one(
        db,
        """
        SELECT
            c.*,
            v.title AS video_title,
            v.creator_name AS video_creator_name,
            v.source_url AS video_source_url,
            v.cover_url AS video_cover_url,
            CASE WHEN s.card_id IS NULL THEN 0 ELSE 1 END AS is_saved
        FROM video_action_cards c
        JOIN source_videos v ON v.id = c.video_id
        LEFT JOIN user_saved_cards s ON s.card_id = c.id AND s.user_id = ?
        WHERE c.id = ?
        """,
        (user_id, card_id),
    )
    if row is None:
        return None
    return await enrich_card(db, row)


async def list_action_cards(
    db: aiosqlite.Connection,
    user_id: str = DEMO_USER_ID,
) -> list[dict[str, Any]]:
    rows = await fetch_all(
        db,
        """
        SELECT
            c.*,
            v.title AS video_title,
            v.creator_name AS video_creator_name,
            v.source_url AS video_source_url,
            v.cover_url AS video_cover_url,
            CASE WHEN s.card_id IS NULL THEN 0 ELSE 1 END AS is_saved
        FROM video_action_cards c
        JOIN source_videos v ON v.id = c.video_id
        LEFT JOIN user_saved_cards s ON s.card_id = c.id AND s.user_id = ?
        WHERE NOT (
            c.id IN ('lateral-raise', 'front-raise', 'reverse-fly', 'lat-pulldown')
            AND EXISTS (
                SELECT 1 FROM video_action_cards replacement
                WHERE replacement.video_id = c.video_id
                  AND replacement.id LIKE 'video_%_demo'
            )
        )
        ORDER BY c.created_at ASC
        """,
        (user_id,),
    )
    return [await enrich_card(db, row) for row in rows]


async def enrich_card(db: aiosqlite.Connection, row: dict[str, Any]) -> dict[str, Any]:
    summary = await fetch_one(
        db,
        """
        SELECT
            exercise_id,
            COALESCE(SUM(mention_count), 0) AS comment_count,
            COALESCE(MAX(source_video_count), 0) AS source_video_count
        FROM peer_experience_clusters
        WHERE exercise_id = ?
        GROUP BY exercise_id
        """,
        (row["exercise_id"],),
    )
    return {
        "id": row["id"],
        "video_id": row["video_id"],
        "exercise_id": row["exercise_id"],
        "action_name": row["action_name"],
        "body_region": row["body_region"],
        "primary_muscles": json_list(row["primary_muscles"]),
        "secondary_muscles": json_list(row["secondary_muscles"]),
        "equipment": json_list(row["equipment"]),
        "status": row["status"],
        "card_data": json.loads(row["card_data"]),
        "is_saved": bool(row.get("is_saved")),
        "source_video": {
            "id": row["video_id"],
            "title": row["video_title"],
            "creator_name": row["video_creator_name"],
            "source_url": row["video_source_url"],
            "cover_url": row["video_cover_url"],
        },
        "experience_summary": summary,
    }


async def get_card_by_video(db: aiosqlite.Connection, video_id: str) -> dict[str, Any] | None:
    row = await fetch_one(
        db,
        "SELECT id FROM video_action_cards WHERE video_id = ? ORDER BY created_at LIMIT 1",
        (video_id,),
    )
    if row is None:
        return None
    return await get_action_card(db, row["id"])


async def set_saved_card(db: aiosqlite.Connection, card_id: str, saved: bool) -> None:
    if saved:
        await db.execute(
            "INSERT OR IGNORE INTO user_saved_cards (user_id, card_id) VALUES (?, ?)",
            (DEMO_USER_ID, card_id),
        )
    else:
        await db.execute(
            "DELETE FROM user_saved_cards WHERE user_id = ? AND card_id = ?",
            (DEMO_USER_ID, card_id),
        )
    await db.commit()


async def summarize_plan(db: aiosqlite.Connection, plan: dict[str, Any]) -> dict[str, Any]:
    items = await get_plan_items(db, plan["id"])
    regions: list[str] = []
    names: list[str] = []
    for item in items:
        card = item["card"]
        if card["body_region"] not in regions:
            regions.append(card["body_region"])
        names.append(card["action_name"])
    return {
        **plan,
        "item_count": len(items),
        "body_regions": regions,
        "card_names": names[:3],
        "items": items,
    }


async def list_plans(db: aiosqlite.Connection) -> list[dict[str, Any]]:
    rows = await fetch_all(
        db,
        """
        SELECT * FROM training_plans
        WHERE user_id = ? AND status != 'ARCHIVED'
        ORDER BY updated_at DESC
        """,
        (DEMO_USER_ID,),
    )
    return [await summarize_plan(db, row) for row in rows]


async def get_plan(db: aiosqlite.Connection, plan_id: str) -> dict[str, Any] | None:
    row = await fetch_one(
        db,
        "SELECT * FROM training_plans WHERE id = ? AND user_id = ?",
        (plan_id, DEMO_USER_ID),
    )
    if row is None:
        return None
    return await summarize_plan(db, row)


async def get_plan_items(db: aiosqlite.Connection, plan_id: str) -> list[dict[str, Any]]:
    rows = await fetch_all(
        db,
        """
        SELECT * FROM training_plan_items
        WHERE plan_id = ?
        ORDER BY sort_order ASC
        """,
        (plan_id,),
    )
    items = []
    for row in rows:
        card = await get_action_card(db, row["card_id"])
        if card is not None:
            items.append({**row, "card": card})
    return items


async def create_plan(
    db: aiosqlite.Connection,
    name: str | None,
    initial_card_id: str | None,
) -> dict[str, Any]:
    plan_id = new_id("plan")
    await db.execute(
        "INSERT INTO training_plans (id, user_id, name) VALUES (?, ?, ?)",
        (plan_id, DEMO_USER_ID, name or "未命名练单"),
    )
    if initial_card_id:
        await add_plan_item(db, plan_id, initial_card_id, commit=False)
    await db.commit()
    plan = await get_plan(db, plan_id)
    assert plan is not None
    return plan


async def update_plan(
    db: aiosqlite.Connection,
    plan_id: str,
    name: str | None,
    status: str | None,
    ordered_item_ids: list[str] | None,
) -> dict[str, Any] | None:
    plan = await get_plan(db, plan_id)
    if plan is None:
        return None
    if name is not None:
        await db.execute(
            "UPDATE training_plans SET name = ?, updated_at = datetime('now') WHERE id = ?",
            (name, plan_id),
        )
    if status is not None:
        await db.execute(
            "UPDATE training_plans SET status = ?, updated_at = datetime('now') WHERE id = ?",
            (status, plan_id),
        )
    if ordered_item_ids is not None:
        for index, item_id in enumerate(ordered_item_ids):
            await db.execute(
                """
                UPDATE training_plan_items
                SET sort_order = ?
                WHERE id = ? AND plan_id = ?
                """,
                (index, item_id, plan_id),
            )
        await db.execute(
            "UPDATE training_plans SET updated_at = datetime('now') WHERE id = ?",
            (plan_id,),
        )
    await db.commit()
    return await get_plan(db, plan_id)


async def add_plan_item(
    db: aiosqlite.Connection,
    plan_id: str,
    card_id: str,
    commit: bool = True,
) -> dict[str, Any] | None:
    exists = await fetch_one(
        db,
        "SELECT id FROM training_plan_items WHERE plan_id = ? AND card_id = ?",
        (plan_id, card_id),
    )
    if exists is not None:
        return await get_plan(db, plan_id)
    next_order = await fetch_one(
        db,
        "SELECT COALESCE(MAX(sort_order) + 1, 0) AS sort_order FROM training_plan_items WHERE plan_id = ?",
        (plan_id,),
    )
    await db.execute(
        """
        INSERT INTO training_plan_items (id, plan_id, card_id, sort_order)
        VALUES (?, ?, ?, ?)
        """,
        (new_id("plan_item"), plan_id, card_id, next_order["sort_order"]),
    )
    await db.execute(
        "UPDATE training_plans SET status = 'SAVED', updated_at = datetime('now') WHERE id = ?",
        (plan_id,),
    )
    if commit:
        await db.commit()
    return await get_plan(db, plan_id)


async def delete_plan_item(db: aiosqlite.Connection, plan_id: str, item_id: str) -> dict[str, Any] | None:
    await db.execute(
        "DELETE FROM training_plan_items WHERE id = ? AND plan_id = ?",
        (item_id, plan_id),
    )
    rows = await fetch_all(
        db,
        "SELECT id FROM training_plan_items WHERE plan_id = ? ORDER BY sort_order ASC",
        (plan_id,),
    )
    for index, row in enumerate(rows):
        await db.execute(
            "UPDATE training_plan_items SET sort_order = ? WHERE id = ?",
            (index, row["id"]),
        )
    await db.execute(
        "UPDATE training_plans SET updated_at = datetime('now') WHERE id = ?",
        (plan_id,),
    )
    await db.commit()
    return await get_plan(db, plan_id)


async def active_session(db: aiosqlite.Connection) -> dict[str, Any] | None:
    row = await fetch_one(
        db,
        """
        SELECT s.*, p.name AS plan_name
        FROM training_sessions s
        JOIN training_plans p ON p.id = s.plan_id
        WHERE s.user_id = ? AND s.status = 'IN_PROGRESS'
        ORDER BY s.started_at DESC
        LIMIT 1
        """,
        (DEMO_USER_ID,),
    )
    if row is None:
        return None
    counts = await session_counts(db, row["id"])
    return {**row, **counts}


async def session_counts(db: aiosqlite.Connection, session_id: str) -> dict[str, int]:
    row = await fetch_one(
        db,
        """
        SELECT
            COUNT(*) AS total_count,
            SUM(CASE WHEN item_status != 'PENDING' THEN 1 ELSE 0 END) AS completed_count
        FROM training_session_items
        WHERE session_id = ?
        """,
        (session_id,),
    )
    return {
        "total_count": int(row["total_count"] or 0),
        "completed_count": int(row["completed_count"] or 0),
    }


async def create_session(db: aiosqlite.Connection, plan_id: str) -> dict[str, Any] | None:
    plan = await get_plan(db, plan_id)
    if plan is None or not plan["items"]:
        return None
    existing = await active_session(db)
    if existing is not None:
        return await get_session(db, existing["id"])
    session_id = new_id("session")
    await db.execute(
        "INSERT INTO training_sessions (id, user_id, plan_id) VALUES (?, ?, ?)",
        (session_id, DEMO_USER_ID, plan_id),
    )
    for item in plan["items"]:
        await db.execute(
            """
            INSERT INTO training_session_items (id, session_id, card_id, sort_order)
            VALUES (?, ?, ?, ?)
            """,
            (new_id("session_item"), session_id, item["card_id"], item["sort_order"]),
        )
    await db.execute(
        """
        UPDATE training_plans
        SET last_used_at = datetime('now'), use_count = use_count + 1, updated_at = datetime('now')
        WHERE id = ?
        """,
        (plan_id,),
    )
    await db.commit()
    return await get_session(db, session_id)


async def get_session(db: aiosqlite.Connection, session_id: str) -> dict[str, Any] | None:
    row = await fetch_one(
        db,
        """
        SELECT s.*, p.name AS plan_name
        FROM training_sessions s
        JOIN training_plans p ON p.id = s.plan_id
        WHERE s.id = ? AND s.user_id = ?
        """,
        (session_id, DEMO_USER_ID),
    )
    if row is None:
        return None
    items = await get_session_items(db, session_id)
    counts = await session_counts(db, session_id)
    return {**row, **counts, "items": items}


async def get_session_items(db: aiosqlite.Connection, session_id: str) -> list[dict[str, Any]]:
    rows = await fetch_all(
        db,
        "SELECT * FROM training_session_items WHERE session_id = ? ORDER BY sort_order ASC",
        (session_id,),
    )
    items = []
    for row in rows:
        card = await get_action_card(db, row["card_id"])
        if card is not None:
            items.append({**row, "felt_muscles": json_list(row["felt_muscles"]), "card": card})
    return items


async def update_session_item(
    db: aiosqlite.Connection,
    session_id: str,
    item_id: str,
    item_status: str | None,
    feedback_type: str | None,
    felt_muscles: list[str] | None,
) -> dict[str, Any] | None:
    item = await fetch_one(
        db,
        "SELECT * FROM training_session_items WHERE id = ? AND session_id = ?",
        (item_id, session_id),
    )
    if item is None:
        return None
    final_status = item_status
    if feedback_type == "DISCOMFORT":
        final_status = "STOPPED_FOR_DISCOMFORT"
    elif feedback_type is not None and final_status is None:
        final_status = "COMPLETED"
    await db.execute(
        """
        UPDATE training_session_items
        SET item_status = COALESCE(?, item_status),
            feedback_type = COALESCE(?, feedback_type),
            felt_muscles = COALESCE(?, felt_muscles),
            feedback_at = CASE WHEN ? IS NULL THEN feedback_at ELSE datetime('now') END
        WHERE id = ? AND session_id = ?
        """,
        (
            final_status,
            feedback_type,
            json.dumps(felt_muscles, ensure_ascii=False) if felt_muscles is not None else None,
            feedback_type,
            item_id,
            session_id,
        ),
    )
    await refresh_session_progress(db, session_id)
    await db.commit()
    return await get_session(db, session_id)


async def end_session(db: aiosqlite.Connection, session_id: str) -> dict[str, Any] | None:
    session = await get_session(db, session_id)
    if session is None:
        return None
    await db.execute(
        """
        UPDATE training_sessions
        SET status = 'ENDED', completed_at = COALESCE(completed_at, datetime('now'))
        WHERE id = ? AND user_id = ?
        """,
        (session_id, DEMO_USER_ID),
    )
    await db.commit()
    return await get_session(db, session_id)


async def refresh_session_progress(db: aiosqlite.Connection, session_id: str) -> None:
    pending = await fetch_one(
        db,
        """
        SELECT sort_order FROM training_session_items
        WHERE session_id = ? AND item_status = 'PENDING'
        ORDER BY sort_order ASC
        LIMIT 1
        """,
        (session_id,),
    )
    if pending is None:
        await db.execute(
            """
            UPDATE training_sessions
            SET status = 'COMPLETED', completed_at = COALESCE(completed_at, datetime('now'))
            WHERE id = ?
            """,
            (session_id,),
        )
    else:
        await db.execute(
            "UPDATE training_sessions SET current_index = ? WHERE id = ?",
            (pending["sort_order"], session_id),
        )


async def list_experience_groups(
    db: aiosqlite.Connection,
    exercise_id: str,
    problem_tag: str,
) -> tuple[dict[str, Any] | None, list[dict[str, Any]]]:
    exercise = await fetch_one(db, "SELECT * FROM standard_exercises WHERE id = ?", (exercise_id,))
    groups = await fetch_all(
        db,
        """
        SELECT * FROM peer_experience_clusters
        WHERE exercise_id = ? AND problem_tag = ?
          AND id NOT IN ('cluster_arms_felt_more_2', 'cluster_arms_felt_more_3')
        ORDER BY mention_count DESC
        """,
        (exercise_id, problem_tag),
    )
    enriched = []
    for group in groups:
        comments = await fetch_all(
            db,
            """
            SELECT
                pc.*,
                v.title AS video_title,
                v.creator_name AS video_creator_name,
                v.source_url AS video_source_url,
                v.cover_url AS video_cover_url
            FROM peer_experience_comments pc
            JOIN source_videos v ON v.id = pc.source_video_id
            WHERE pc.cluster_id = ?
            ORDER BY pc.created_at ASC
            """,
            (group["id"],),
        )
        enriched.append({**group, "comments": comments})
    return exercise, enriched


async def me_summary(db: aiosqlite.Connection) -> dict[str, Any]:
    user = await fetch_one(db, "SELECT * FROM demo_users WHERE id = ?", (DEMO_USER_ID,))
    completed = await fetch_one(
        db,
        """
        SELECT
            COUNT(DISTINCT s.id) AS completed_session_count,
            COUNT(i.id) AS completed_action_count
        FROM training_sessions s
        LEFT JOIN training_session_items i ON i.session_id = s.id AND i.item_status != 'PENDING'
        WHERE s.user_id = ? AND s.status = 'COMPLETED'
        """,
        (DEMO_USER_ID,),
    )
    recent = await fetch_all(
        db,
        """
        SELECT c.action_name, c.body_region, i.feedback_type
        FROM training_session_items i
        JOIN training_sessions s ON s.id = i.session_id
        JOIN video_action_cards c ON c.id = i.card_id
        WHERE s.user_id = ? AND i.item_status != 'PENDING'
        ORDER BY COALESCE(i.feedback_at, s.started_at) DESC
        LIMIT 5
        """,
        (DEMO_USER_ID,),
    )
    regions: list[str] = []
    actions: list[str] = []
    has_discomfort = False
    for row in recent:
        if row["body_region"] not in regions:
            regions.append(row["body_region"])
        actions.append(row["action_name"])
        has_discomfort = has_discomfort or row["feedback_type"] == "DISCOMFORT"
    return {
        "user_id": DEMO_USER_ID,
        "nickname": user["nickname"] if user else "Demo",
        "completed_session_count": int(completed["completed_session_count"] or 0),
        "completed_action_count": int(completed["completed_action_count"] or 0),
        "recent_body_regions": regions,
        "recent_actions": actions,
        "has_discomfort_record": has_discomfort,
    }
