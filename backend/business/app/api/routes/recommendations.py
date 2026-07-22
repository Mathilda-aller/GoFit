from __future__ import annotations

import aiosqlite
from fastapi import APIRouter, Depends, Query

from app.db.database import get_db
from app.schemas.models import RecommendationResult
from app.services.recommendations import recommend_for_plan

router = APIRouter(tags=["recommendations"])


@router.get("/recommendations", response_model=RecommendationResult)
async def recommendations(
    plan_id: str = Query(alias="planId"),
    db: aiosqlite.Connection = Depends(get_db),
) -> dict:
    return await recommend_for_plan(db, plan_id)
