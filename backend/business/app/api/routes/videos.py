from __future__ import annotations

import asyncio
import json
from urllib.parse import quote

import aiosqlite
import httpx
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse

from app.core.config import settings
from app.core.storage import resolve_curated_path, resolve_video_path
from app.db.database import get_db
from app.repositories import business as repo
from app.schemas.models import ImportVideoRequest, ImportVideoResult, ProcessingStatus
from app.services.curated_media import (
    ACTION_TO_EXERCISE,
    CuratedManifest,
    fingerprint_video,
    load_manifest_for_fingerprint,
    load_manifest_for_video,
)

router = APIRouter(tags=["videos"])
_import_locks: dict[str, asyncio.Lock] = {}


def _media_url(file_name: str | None) -> str | None:
    return f"/api/v1/media/videos/{quote(file_name)}" if file_name else None


def _curated_media_url(relative_path: str) -> str:
    return f"/api/v1/media/curated/{quote(relative_path, safe='/')}"


async def _claim_import(
    db: aiosqlite.Connection,
    manifest: CuratedManifest,
    video_id: str,
):
    """Atomically claim one in-flight AI job per immutable video id."""
    lock = _import_locks.setdefault(video_id, asyncio.Lock())
    async with lock:
        active_task = await repo.fetch_one(
            db,
            """
            SELECT * FROM processing_tasks
            WHERE video_id = ? AND status IN ('PENDING', 'QUEUED', 'RUNNING')
            ORDER BY created_at DESC, rowid DESC
            LIMIT 1
            """,
            (video_id,),
        )
        if active_task is not None:
            return active_task, None, active_task["id"], active_task["status"]

        await db.execute(
            """
            INSERT INTO source_videos (id, title, creator_name, source_url)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(id) DO UPDATE SET
                title = excluded.title,
                creator_name = excluded.creator_name,
                source_url = excluded.source_url
            """,
            (video_id, manifest.title, manifest.creator_name, manifest.source_url),
        )
        card = await repo.get_card_by_video(db, video_id)
        existing_source = card["card_data"].get("contentSource") if card else None
        reusable_card = card if existing_source == "AI" else None
        task_id = repo.new_id("task")
        status = "COMPLETED" if reusable_card else "PENDING"
        await db.execute(
            """
            INSERT INTO processing_tasks (id, video_id, status, result_card_id)
            VALUES (?, ?, ?, ?)
            """,
            (task_id, video_id, status, reusable_card["id"] if reusable_card else None),
        )
        await db.commit()
        return None, reusable_card, task_id, status


def _curated_card_data(manifest: CuratedManifest) -> dict:
    def item(clip) -> dict:
        return {
            "candidateId": clip.candidate_id,
            "startMs": clip.source_start_ms,
            "endMs": clip.source_end_ms,
            "mediaUrl": _curated_media_url(clip.relative_path),
        }

    return {
        "correctDemo": item(manifest.correct_clip),
        "errorDemos": [item(clip) for clip in manifest.error_clips],
    }


def _media_artifacts(manifest: CuratedManifest, artifacts: list[dict]) -> list[dict]:
    urls = {
        manifest.correct_clip.candidate_id: _curated_media_url(manifest.correct_clip.relative_path),
        **{clip.candidate_id: _curated_media_url(clip.relative_path) for clip in manifest.error_clips},
    }
    return [
        {**artifact, "mediaUrl": urls.get(artifact.get("candidateId"))}
        for artifact in artifacts
    ]


async def _ai_job_payload(
    db: aiosqlite.Connection,
    manifest: CuratedManifest,
    *,
    video_id: str,
    task_id: str,
) -> dict:
    video_path = resolve_video_path(manifest.source_file_name)
    exercise = await repo.fetch_one(
        db,
        "SELECT * FROM standard_exercises WHERE id = ?",
        (ACTION_TO_EXERCISE[manifest.standard_action_id],),
    )
    if exercise is None:
        raise HTTPException(status_code=422, detail="Manifest standard action is not configured.")
    return {
        "requestId": task_id,
        "sourceVideo": {
            "videoId": video_id,
            "title": manifest.title,
            "creatorName": manifest.creator_name,
            "sourceUrl": manifest.source_url,
        },
        "videoPath": str(video_path),
        "standardActionCandidates": [{
            "standardActionId": manifest.standard_action_id,
            "name": exercise["name"],
            "aliases": [],
            "bodyRegion": exercise["body_region"],
            "primaryMuscles": json.loads(exercise["primary_muscles"]),
            "secondaryMuscles": json.loads(exercise["secondary_muscles"]),
            "equipment": json.loads(exercise["equipment"]),
        }],
        "curatedMedia": {
            "correctClip": manifest.correct_clip.ai_payload(),
            "errorClips": [clip.ai_payload() for clip in manifest.error_clips],
        },
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
    manifest: CuratedManifest,
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
        "contentSource": "AI",
        "aiResult": build_result,
        "sourceMediaUrl": _media_url(manifest.source_file_name),
        "curatedMedia": _curated_card_data(manifest),
        "mediaArtifacts": _media_artifacts(manifest, result.get("mediaArtifacts", [])),
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


async def _persist_mock_fallback(
    db: aiosqlite.Connection,
    *,
    task_id: str,
    video_id: str,
    manifest: CuratedManifest,
    reason: str,
) -> str:
    exercise_id = ACTION_TO_EXERCISE[manifest.standard_action_id]
    exercise = await repo.fetch_one(db, "SELECT * FROM standard_exercises WHERE id = ?", (exercise_id,))
    if exercise is None:
        raise HTTPException(status_code=422, detail="Manifest standard action is not configured.")
    seed = await repo.fetch_one(
        db,
        "SELECT card_data FROM video_action_cards WHERE exercise_id = ? ORDER BY created_at LIMIT 1",
        (exercise_id,),
    )
    seed_data = json.loads(seed["card_data"]) if seed else {}
    raw_steps = seed_data.get("steps") or [[f"完成{manifest.action_name}的准备姿势", "00:00"], ["保持动作路径稳定", "00:01"], ["控制速度回到起点", "00:02"]]
    fallback_evidence = ["mock_fallback_text"]
    correct = {
        "kind": "CORRECT_DEMO",
        "candidateId": manifest.correct_clip.candidate_id,
        "startMs": manifest.correct_clip.source_start_ms,
        "endMs": manifest.correct_clip.source_end_ms,
        "evidenceIds": [f"curated_{manifest.correct_clip.candidate_id}"],
    }
    errors = []
    for index, clip in enumerate(manifest.error_clips, start=1):
        media = {
            "kind": "ERROR_DEMO",
            "candidateId": clip.candidate_id,
            "startMs": clip.source_start_ms,
            "endMs": clip.source_end_ms,
            "evidenceIds": [f"curated_{clip.candidate_id}"],
        }
        errors.append({
            "mistake": f"错误示范 {index}",
            "correction": "请对照正确示范调整动作；当前文字为模型失败后的示例内容。",
            "errorDemo": media,
            "evidenceIds": media["evidenceIds"],
        })
    steps = []
    for index, raw in enumerate(raw_steps[:5], start=1):
        instruction = raw[0] if isinstance(raw, list) and raw else str(raw)
        steps.append({
            "order": index,
            "instruction": instruction,
            "startMs": manifest.correct_clip.source_start_ms,
            "endMs": manifest.correct_clip.source_end_ms,
            "evidenceIds": fallback_evidence,
        })
    while len(steps) < 3:
        steps.append({**steps[-1], "order": len(steps) + 1})
    cue = seed_data.get("cue") or f"稳定完成 {manifest.action_name}"
    tip = seed_data.get("tip") or "保持动作稳定，如有不适请停止训练。"
    source_video = {
        "videoId": video_id,
        "title": manifest.title,
        "creatorName": manifest.creator_name,
        "sourceUrl": manifest.source_url,
    }
    build_result = {
        "schemaVersion": "1.1.0",
        "requestId": task_id,
        "status": "NEEDS_REVIEW",
        "standardAction": {"standardActionId": manifest.standard_action_id, "confidence": 1, "decision": "NEEDS_REVIEW"},
        "actionCard": {
            "sourceVideo": source_video,
            "actionName": exercise["name"],
            "bodyRegion": exercise["body_region"],
            "primaryMuscles": json.loads(exercise["primary_muscles"]),
            "secondaryMuscles": json.loads(exercise["secondary_muscles"]),
            "equipment": json.loads(exercise["equipment"]),
            "learningSide": {"correctDemo": correct, "steps": steps, "keyReminders": [{"text": tip, "evidenceIds": fallback_evidence}], "commonErrors": errors},
            "trainingSide": {"loopDemo": correct, "quickCue": {"text": cue, "evidenceIds": fallback_evidence}, "quickTips": [{"text": tip, "evidenceIds": fallback_evidence}]},
        },
        "warnings": ["真实 AI 生成失败，当前展示示例文案。"],
        "needsReviewReasons": [reason],
        "provider": {"name": "mock-fallback", "version": "1.0.0"},
    }
    card_id = f"mock-{video_id}"
    card_data = {
        "creator": manifest.creator_name,
        "title": manifest.title,
        "source": "来自本视频 · 示例文案",
        "cue": cue,
        "steps": raw_steps,
        "tip": tip,
        "contentSource": "MOCK_FALLBACK",
        "fallbackReason": reason,
        "aiResult": build_result,
        "sourceMediaUrl": _media_url(manifest.source_file_name),
        "curatedMedia": _curated_card_data(manifest),
    }
    await db.execute(
        """
        INSERT INTO video_action_cards
        (id, video_id, exercise_id, action_name, body_region, primary_muscles,
         secondary_muscles, equipment, card_data, status)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 'NEEDS_REVIEW')
        ON CONFLICT(id) DO UPDATE SET card_data = excluded.card_data, status = excluded.status
        """,
        (card_id, video_id, exercise_id, exercise["name"], exercise["body_region"], exercise["primary_muscles"], exercise["secondary_muscles"], exercise["equipment"], json.dumps(card_data, ensure_ascii=False)),
    )
    await db.execute(
        "UPDATE processing_tasks SET status = 'COMPLETED', result_card_id = ?, error_message = ?, updated_at = datetime('now') WHERE id = ?",
        (card_id, reason, task_id),
    )
    await db.commit()
    return card_id


@router.get("/media/videos/{file_name}")
async def read_video(file_name: str) -> FileResponse:
    path = resolve_video_path(file_name)
    return FileResponse(path, media_type="video/mp4")


@router.get("/media/curated/{relative_path:path}")
async def read_curated_video(relative_path: str) -> FileResponse:
    return FileResponse(resolve_curated_path(relative_path), media_type="video/mp4")


@router.post("/videos/import", response_model=ImportVideoResult)
async def import_video(
    request: ImportVideoRequest,
    db: aiosqlite.Connection = Depends(get_db),
) -> dict:
    if not request.asset_file_name:
        raise HTTPException(status_code=422, detail="assetFileName is required for curated import.")
    manifest = load_manifest_for_video(request.asset_file_name)
    video_id = fingerprint_video(manifest)

    active_task, reusable_card, task_id, status = await _claim_import(db, manifest, video_id)
    if active_task is not None:
        return {
            "video_id": video_id,
            "task_id": active_task["id"],
            "status": active_task["status"],
            "card_id": active_task["result_card_id"],
            "message": "这条视频正在 AI 中心处理中。",
            "media_url": _media_url(manifest.source_file_name),
            "content_source": None,
            "fallback_reason": None,
        }

    message = "这条视频已经整理成动作卡。" if reusable_card else "已提交 AI 中心处理。"
    fallback_reason = None
    if reusable_card is None:
        payload = await _ai_job_payload(db, manifest, video_id=video_id, task_id=task_id)
        try:
            async with httpx.AsyncClient(timeout=10, trust_env=False) as client:
                response = await client.post(
                    f"{settings.ai_center_url}/internal/v1/action-card-jobs",
                    json=payload,
                )
                response.raise_for_status()
                ai_job = response.json()
            status = ai_job["status"]
            if status == "COMPLETED":
                card_id = await _persist_ai_result(db, task_id=task_id, video_id=video_id, job=ai_job, manifest=manifest)
                reusable_card = await repo.get_action_card(db, card_id)
            elif status == "FAILED":
                fallback_reason = ai_job.get("error", {}).get("message") or "AI workflow failed."
                card_id = await _persist_mock_fallback(db, task_id=task_id, video_id=video_id, manifest=manifest, reason=fallback_reason)
                reusable_card = await repo.get_action_card(db, card_id)
                status = "COMPLETED"
                message = "AI 处理失败，已返回带人工示范的示例文案。"
            else:
                await db.execute(
                    "UPDATE processing_tasks SET status = ?, updated_at = datetime('now') WHERE id = ?",
                    (status, task_id),
                )
                await db.commit()
        except (httpx.HTTPError, KeyError, ValueError) as exc:
            fallback_reason = str(exc)
            card_id = await _persist_mock_fallback(db, task_id=task_id, video_id=video_id, manifest=manifest, reason=fallback_reason)
            status = "COMPLETED"
            message = "AI 中心暂时不可用，已返回带人工示范的示例文案。"
            reusable_card = await repo.get_action_card(db, card_id)
    return {
        "video_id": video_id,
        "task_id": task_id,
        "status": status,
        "card_id": reusable_card["id"] if reusable_card else None,
        "message": message,
        "media_url": _media_url(manifest.source_file_name),
        "content_source": reusable_card["card_data"].get("contentSource") if reusable_card else None,
        "fallback_reason": fallback_reason,
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
        ORDER BY created_at DESC, rowid DESC
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
            "content_source": card["card_data"].get("contentSource"),
            "fallback_reason": card["card_data"].get("fallbackReason"),
        }
    if task["status"] == "COMPLETED" and task["result_card_id"]:
        card = await repo.get_action_card(db, task["result_card_id"])
        return {
            "task_id": task["id"],
            "video_id": video_id,
            "status": "COMPLETED",
            "card_id": task["result_card_id"],
            "error_message": task["error_message"],
            "content_source": card["card_data"].get("contentSource") if card else None,
            "fallback_reason": card["card_data"].get("fallbackReason") if card else None,
        }
    if task["status"] in {"PENDING", "QUEUED", "RUNNING"}:
        try:
            async with httpx.AsyncClient(timeout=5, trust_env=False) as client:
                response = await client.get(
                    f"{settings.ai_center_url}/internal/v1/action-card-jobs/{task['id']}"
                )
                response.raise_for_status()
                job = response.json()
            ai_status = job["status"]
            if ai_status == "COMPLETED":
                manifest = load_manifest_for_fingerprint(video_id)
                card_id = await _persist_ai_result(
                    db,
                    task_id=task["id"],
                    video_id=video_id,
                    job=job,
                    manifest=manifest,
                )
                return {
                    "task_id": task["id"],
                    "video_id": video_id,
                    "status": "COMPLETED",
                    "card_id": card_id,
                    "error_message": None,
                    "content_source": "AI",
                    "fallback_reason": None,
                }
            if ai_status == "FAILED":
                reason = job.get("error", {}).get("message") or "AI workflow failed."
                manifest = load_manifest_for_fingerprint(video_id)
                card_id = await _persist_mock_fallback(db, task_id=task["id"], video_id=video_id, manifest=manifest, reason=reason)
                return {"task_id": task["id"], "video_id": video_id, "status": "COMPLETED", "card_id": card_id, "error_message": reason, "content_source": "MOCK_FALLBACK", "fallback_reason": reason}
            error_message = job.get("error", {}).get("message") if job.get("error") else None
            await db.execute(
                "UPDATE processing_tasks SET status = ?, error_message = ?, updated_at = datetime('now') WHERE id = ?",
                (ai_status, error_message, task["id"]),
            )
            await db.commit()
            task = {**dict(task), "status": ai_status, "error_message": error_message}
        except (httpx.HTTPError, KeyError, ValueError) as exc:
            reason = str(exc)
            manifest = load_manifest_for_fingerprint(video_id)
            card_id = await _persist_mock_fallback(
                db,
                task_id=task["id"],
                video_id=video_id,
                manifest=manifest,
                reason=reason,
            )
            return {
                "task_id": task["id"],
                "video_id": video_id,
                "status": "COMPLETED",
                "card_id": card_id,
                "error_message": reason,
                "content_source": "MOCK_FALLBACK",
                "fallback_reason": reason,
            }
    return {
        "task_id": task["id"],
        "video_id": task["video_id"],
        "status": task["status"],
        "card_id": task["result_card_id"],
        "error_message": task["error_message"],
        "content_source": None,
        "fallback_reason": None,
    }
