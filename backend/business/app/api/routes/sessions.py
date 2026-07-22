from __future__ import annotations

import aiosqlite
from fastapi import APIRouter, Depends, HTTPException

from app.db.database import get_db
from app.repositories import business as repo
from app.schemas.models import (
    FeedbackResult,
    SubmitFeedbackRequest,
    TrainingSession,
    UpdateSessionItemRequest,
)
from app.services.feedback import is_safety_feedback, problem_tag_for_feedback

router = APIRouter(tags=["sessions"])


@router.post("/plans/{plan_id}/sessions", response_model=TrainingSession)
async def create_session(
    plan_id: str,
    db: aiosqlite.Connection = Depends(get_db),
) -> dict:
    session = await repo.create_session(db, plan_id)
    if session is None:
        raise HTTPException(status_code=404, detail="Training plan not found or has no items.")
    return session


@router.get("/sessions/{session_id}", response_model=TrainingSession)
async def get_session(
    session_id: str,
    db: aiosqlite.Connection = Depends(get_db),
) -> dict:
    session = await repo.get_session(db, session_id)
    if session is None:
        raise HTTPException(status_code=404, detail="Training session not found.")
    return session


@router.post("/sessions/{session_id}/end", response_model=TrainingSession)
async def end_session(
    session_id: str,
    db: aiosqlite.Connection = Depends(get_db),
) -> dict:
    session = await repo.end_session(db, session_id)
    if session is None:
        raise HTTPException(status_code=404, detail="Training session not found.")
    return session


@router.patch("/sessions/{session_id}/items/{item_id}", response_model=TrainingSession)
async def update_session_item(
    session_id: str,
    item_id: str,
    request: UpdateSessionItemRequest,
    db: aiosqlite.Connection = Depends(get_db),
) -> dict:
    session = await repo.update_session_item(
        db,
        session_id,
        item_id,
        request.item_status,
        request.feedback_type,
        request.felt_muscles,
    )
    if session is None:
        raise HTTPException(status_code=404, detail="Training session item not found.")
    return session


@router.post("/sessions/{session_id}/feedback", response_model=FeedbackResult)
async def submit_feedback(
    session_id: str,
    request: SubmitFeedbackRequest,
    db: aiosqlite.Connection = Depends(get_db),
) -> dict:
    problem_tag = problem_tag_for_feedback(request.feedback_type, request.felt_muscles)
    session = await repo.update_session_item(
        db,
        session_id,
        request.item_id,
        None,
        request.feedback_type,
        request.felt_muscles,
    )
    if session is None:
        raise HTTPException(status_code=404, detail="Training session item not found.")
    next_item_id = None
    if session["status"] == "IN_PROGRESS":
        for item in session["items"]:
            if item["item_status"] == "PENDING":
                next_item_id = item["id"]
                break
    return {
        "session": session,
        "problem_tag": problem_tag,
        "should_show_safety": is_safety_feedback(request.feedback_type),
        "next_item_id": next_item_id,
    }
