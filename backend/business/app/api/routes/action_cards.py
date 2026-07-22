from __future__ import annotations

import aiosqlite
from fastapi import APIRouter, Depends, HTTPException

from app.db.database import get_db
from app.repositories import business as repo
from app.schemas.models import ActionCard, ActionCardList

router = APIRouter(tags=["action-cards"])


@router.get("/action-cards", response_model=ActionCardList)
async def list_action_cards(db: aiosqlite.Connection = Depends(get_db)) -> dict:
    return {"items": await repo.list_action_cards(db)}


@router.get("/action-cards/{card_id}", response_model=ActionCard)
async def get_action_card(
    card_id: str,
    db: aiosqlite.Connection = Depends(get_db),
) -> dict:
    card = await repo.get_action_card(db, card_id)
    if card is None:
        raise HTTPException(status_code=404, detail="Action card not found.")
    return card


@router.post("/action-cards/{card_id}/saved", response_model=ActionCard)
async def save_action_card(
    card_id: str,
    db: aiosqlite.Connection = Depends(get_db),
) -> dict:
    card = await repo.get_action_card(db, card_id)
    if card is None:
        raise HTTPException(status_code=404, detail="Action card not found.")
    await repo.set_saved_card(db, card_id, saved=True)
    saved_card = await repo.get_action_card(db, card_id)
    assert saved_card is not None
    return saved_card


@router.delete("/action-cards/{card_id}/saved", response_model=ActionCard)
async def unsave_action_card(
    card_id: str,
    db: aiosqlite.Connection = Depends(get_db),
) -> dict:
    card = await repo.get_action_card(db, card_id)
    if card is None:
        raise HTTPException(status_code=404, detail="Action card not found.")
    await repo.set_saved_card(db, card_id, saved=False)
    unsaved_card = await repo.get_action_card(db, card_id)
    assert unsaved_card is not None
    return unsaved_card
