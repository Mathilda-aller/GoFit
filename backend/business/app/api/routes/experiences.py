from __future__ import annotations

import aiosqlite
from fastapi import APIRouter, Depends, Query

from app.db.database import get_db
from app.schemas.models import ExperienceResult
from app.services.experiences import experience_for

router = APIRouter(tags=["peer-experiences"])


@router.get("/experiences", response_model=ExperienceResult)
async def experiences(
    exercise_id: str = Query(alias="exerciseId"),
    problem_tag: str = Query(default="ARMS_FELT_MORE", alias="problemTag"),
    current_video_id: str | None = Query(default=None, alias="currentVideoId"),
    from_training: bool = Query(default=False, alias="fromTraining"),
    db: aiosqlite.Connection = Depends(get_db),
) -> dict:
    _ = current_video_id, from_training
    return await experience_for(db, exercise_id, problem_tag)
