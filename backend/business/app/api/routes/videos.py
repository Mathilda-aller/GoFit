from __future__ import annotations

import aiosqlite
from fastapi import APIRouter, Depends, HTTPException

from app.db.database import get_db
from app.repositories import business as repo
from app.schemas.models import ImportVideoRequest, ImportVideoResult, ProcessingStatus

router = APIRouter(tags=["videos"])


@router.post("/videos/import", response_model=ImportVideoResult)
async def import_video(
    request: ImportVideoRequest,
    db: aiosqlite.Connection = Depends(get_db),
) -> dict:
    video_id = request.video_id or repo.new_id("video")
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
    return {
        "video_id": video_id,
        "task_id": task_id,
        "status": status,
        "card_id": card["id"] if card else None,
        "message": "这条视频已经整理成动作卡。" if card else "已创建处理任务，等待 AI 处理接入。",
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
    return {
        "task_id": task["id"],
        "video_id": task["video_id"],
        "status": task["status"],
        "card_id": task["result_card_id"],
        "error_message": task["error_message"],
    }
