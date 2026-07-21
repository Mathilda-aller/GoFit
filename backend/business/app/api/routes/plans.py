from __future__ import annotations

import aiosqlite
from fastapi import APIRouter, Depends, HTTPException

from app.db.database import get_db
from app.repositories import business as repo
from app.schemas.models import (
    AddPlanItemRequest,
    CreatePlanRequest,
    PlanList,
    TrainingPlan,
    UpdatePlanRequest,
)

router = APIRouter(tags=["plans"])


@router.get("/plans", response_model=PlanList)
async def list_plans(db: aiosqlite.Connection = Depends(get_db)) -> dict:
    return {
        "active_session": await repo.active_session(db),
        "items": await repo.list_plans(db),
    }


@router.post("/plans", response_model=TrainingPlan)
async def create_plan(
    request: CreatePlanRequest,
    db: aiosqlite.Connection = Depends(get_db),
) -> dict:
    if request.initial_card_id and await repo.get_action_card(db, request.initial_card_id) is None:
        raise HTTPException(status_code=404, detail="Initial action card not found.")
    return await repo.create_plan(db, request.name, request.initial_card_id)


@router.get("/plans/{plan_id}", response_model=TrainingPlan)
async def get_plan(
    plan_id: str,
    db: aiosqlite.Connection = Depends(get_db),
) -> dict:
    plan = await repo.get_plan(db, plan_id)
    if plan is None:
        raise HTTPException(status_code=404, detail="Training plan not found.")
    return plan


@router.patch("/plans/{plan_id}", response_model=TrainingPlan)
async def update_plan(
    plan_id: str,
    request: UpdatePlanRequest,
    db: aiosqlite.Connection = Depends(get_db),
) -> dict:
    plan = await repo.update_plan(db, plan_id, request.name, request.status, request.ordered_item_ids)
    if plan is None:
        raise HTTPException(status_code=404, detail="Training plan not found.")
    return plan


@router.post("/plans/{plan_id}/items", response_model=TrainingPlan)
async def add_plan_item(
    plan_id: str,
    request: AddPlanItemRequest,
    db: aiosqlite.Connection = Depends(get_db),
) -> dict:
    if await repo.get_plan(db, plan_id) is None:
        raise HTTPException(status_code=404, detail="Training plan not found.")
    if await repo.get_action_card(db, request.card_id) is None:
        raise HTTPException(status_code=404, detail="Action card not found.")
    plan = await repo.add_plan_item(db, plan_id, request.card_id)
    assert plan is not None
    return plan


@router.delete("/plans/{plan_id}/items/{item_id}", response_model=TrainingPlan)
async def delete_plan_item(
    plan_id: str,
    item_id: str,
    db: aiosqlite.Connection = Depends(get_db),
) -> dict:
    if await repo.get_plan(db, plan_id) is None:
        raise HTTPException(status_code=404, detail="Training plan not found.")
    plan = await repo.delete_plan_item(db, plan_id, item_id)
    assert plan is not None
    return plan
