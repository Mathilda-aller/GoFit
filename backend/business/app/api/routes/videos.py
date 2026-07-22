from __future__ import annotations

import json
from urllib.parse import quote

import aiosqlite
import httpx
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse

from app.core.config import settings
from app.core.storage import resolve_video_path
from app.db.database import get_db
from app.repositories import business as repo
from app.schemas.models import ImportVideoRequest, ImportVideoResult, ProcessingStatus

router = APIRouter(tags=["videos"])


def _media_url(file_name: str | None) -> str | None:
    return f"/api/v1/media/videos/{quote(file_name)}" if file_name else None


def _ai_job_payload(request: ImportVideoRequest, *, video_id: str, task_id: str) -> dict:
    if not request.asset_file_name:
        raise HTTPException(status_code=422, detail="assetFileName is required for AI processing.")
    video_path = resolve_video_path(request.asset_file_name)
    return {
        "requestId": task_id,
        "sourceVideo": {
            "videoId": video_id,
            "title": request.title or "待处理健身视频",
            "creatorName": request.creator_name or "未知创作者",
            "sourceUrl": request.source_url or f"https://example.test/videos/{video_id}",
        },
        "videoPath": str(video_path),
    }


def _timestamp(milliseconds: int) -> str:
    seconds = max(0, int(milliseconds) // 1000)
    return f"{seconds // 60:02d}:{seconds % 60:02d}"


async def _persist_ai_result(
    db: aiosqlite.Connection,
    *,
    task_id: str,
    video_id: str,
    job: dict,
) -> str:
    result = job["result"]
    build_result = result["actionCardResult"]
    card = build_result["actionCard"]
    match = build_result["standardAction"]
    exercise_id = match["standardActionId"]
    learning = card["learningSide"]
    training = card["trainingSide"]
    card_id = f"ai-{video_id}"

    await db.execute(
        """
        INSERT OR IGNORE INTO standard_exercises
        (id, name, aliases, body_region, primary_muscles, secondary_muscles, equipment)
        VALUES (?, ?, '[]', ?, ?, ?, ?)
        """,
        (
            exercise_id,
            card["actionName"],
            card["bodyRegion"],
            json.dumps(card["primaryMuscles"], ensure_ascii=False),
            json.dumps(card.get("secondaryMuscles", []), ensure_ascii=False),
            json.dumps(card.get("equipment", []), ensure_ascii=False),
        ),
    )
    steps = [
        [item["instruction"], _timestamp(item["startMs"])]
        for item in learning["steps"]
    ]
    reminders = learning.get("keyReminders", [])
    tips = training.get("quickTips", [])
    card_data = {
        "creator": card["sourceVideo"]["creatorName"],
        "title": card["sourceVideo"]["title"],
        "source": "来自本视频 · AI 整理",
        "cue": training["quickCue"]["text"],
        "steps": steps,
        "tip": (reminders or tips or [{"text": "保持动作稳定。"}])[0]["text"],
        "aiResult": build_result,
        "mediaArtifacts": result.get("mediaArtifacts", []),
    }
    await db.execute(
        """
        INSERT INTO video_action_cards
        (id, video_id, exercise_id, action_name, body_region, primary_muscles,
         secondary_muscles, equipment, card_data, status)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(id) DO UPDATE SET card_data = excluded.card_data, status = excluded.status
        """,
        (
            card_id,
            video_id,
            exercise_id,
            card["actionName"],
            card["bodyRegion"],
            json.dumps(card["primaryMuscles"], ensure_ascii=False),
            json.dumps(card.get("secondaryMuscles", []), ensure_ascii=False),
            json.dumps(card.get("equipment", []), ensure_ascii=False),
            json.dumps(card_data, ensure_ascii=False),
            build_result["status"],
        ),
    )
    await db.execute(
        "UPDATE processing_tasks SET status = 'COMPLETED', result_card_id = ?, updated_at = datetime('now') WHERE id = ?",
        (card_id, task_id),
    )
    await db.commit()
    return card_id


@router.get("/media/videos/{file_name}")
async def read_video(file_name: str) -> FileResponse:
    path = resolve_video_path(file_name)
    return FileResponse(path, media_type="video/mp4")


@router.post("/videos/import", response_model=ImportVideoResult)
async def import_video(
    request: ImportVideoRequest,
    db: aiosqlite.Connection = Depends(get_db),
) -> dict:
    video_id = request.video_id or repo.new_id("video")
    if request.asset_file_name:
        resolve_video_path(request.asset_file_name)
    video = await repo.get_source_video(db, video_id)
    if video is None:
        await db.execute(
            """
            INSERT INTO source_videos (id, title, creator_name, source_url)
            VALUES (?, ?, ?, ?)
            """,
            (
                video_id,
                request.title or "待处理健身视频",
                request.creator_name or "未知创作者",
                request.source_url or f"https://example.test/videos/{video_id}",
            ),
        )
    card = await repo.get_card_by_video(db, video_id)
    task_id = repo.new_id("task")
    status = "COMPLETED" if card else "PENDING"
    await db.execute(
        """
        INSERT INTO processing_tasks (id, video_id, status, result_card_id)
        VALUES (?, ?, ?, ?)
        """,
        (task_id, video_id, status, card["id"] if card else None),
    )
    await db.commit()

    message = "这条视频已经整理成动作卡。" if card else "已提交 AI 中心处理。"
    if card is None:
        payload = _ai_job_payload(request, video_id=video_id, task_id=task_id)
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                response = await client.post(
                    f"{settings.ai_center_url}/internal/v1/action-card-jobs",
                    json=payload,
                )
                response.raise_for_status()
                ai_job = response.json()
            status = ai_job["status"]
            await db.execute(
                "UPDATE processing_tasks SET status = ?, updated_at = datetime('now') WHERE id = ?",
                (status, task_id),
            )
            await db.commit()
        except (httpx.HTTPError, KeyError, ValueError) as exc:
            status = "FAILED"
            message = "AI 中心暂时不可用，视频已保留，可稍后重试。"
            await db.execute(
                "UPDATE processing_tasks SET status = 'FAILED', error_message = ?, updated_at = datetime('now') WHERE id = ?",
                (str(exc), task_id),
            )
            await db.commit()
    return {
        "video_id": video_id,
        "task_id": task_id,
        "status": status,
        "card_id": card["id"] if card else None,
        "message": message,
        "media_url": _media_url(request.asset_file_name),
    }


@router.get("/videos/{video_id}/processing", response_model=ProcessingStatus)
async def processing_status(
    video_id: str,
    db: aiosqlite.Connection = Depends(get_db),
) -> dict:
    task = await repo.fetch_one(
        db,
        """
        SELECT * FROM processing_tasks
        WHERE video_id = ?
        ORDER BY created_at DESC
        LIMIT 1
        """,
        (video_id,),
    )
    if task is None:
        card = await repo.get_card_by_video(db, video_id)
        if card is None:
            raise HTTPException(status_code=404, detail="Video processing task not found.")
        return {
            "task_id": "existing_card",
            "video_id": video_id,
            "status": "COMPLETED",
            "card_id": card["id"],
            "error_message": None,
        }
    if task["status"] in {"PENDING", "QUEUED", "RUNNING"}:
        try:
            async with httpx.AsyncClient(timeout=5) as client:
                response = await client.get(
                    f"{settings.ai_center_url}/internal/v1/action-card-jobs/{task['id']}"
                )
                response.raise_for_status()
                job = response.json()
            ai_status = job["status"]
            if ai_status == "COMPLETED":
                card_id = await _persist_ai_result(
                    db,
                    task_id=task["id"],
                    video_id=video_id,
                    job=job,
                )
                return {
                    "task_id": task["id"],
                    "video_id": video_id,
                    "status": "COMPLETED",
                    "card_id": card_id,
                    "error_message": None,
                }
            error_message = job.get("error", {}).get("message") if job.get("error") else None
            await db.execute(
                "UPDATE processing_tasks SET status = ?, error_message = ?, updated_at = datetime('now') WHERE id = ?",
                (ai_status, error_message, task["id"]),
            )
            await db.commit()
            task = {**dict(task), "status": ai_status, "error_message": error_message}
        except httpx.HTTPError:
            pass
    return {
        "task_id": task["id"],
        "video_id": task["video_id"],
        "status": task["status"],
        "card_id": task["result_card_id"],
        "error_message": task["error_message"],
    }
