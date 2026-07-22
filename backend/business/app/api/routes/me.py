from __future__ import annotations

import aiosqlite
from fastapi import APIRouter, Depends

from app.db.database import get_db
from app.repositories import business as repo
from app.schemas.models import MeSummary

router = APIRouter(tags=["me"])


@router.get("/me", response_model=MeSummary)
async def me(db: aiosqlite.Connection = Depends(get_db)) -> dict:
    return await repo.me_summary(db)
