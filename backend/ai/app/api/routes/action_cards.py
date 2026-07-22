from functools import lru_cache

from fastapi import APIRouter, Depends

from app.core.config import get_settings
from app.models.action_card import ActionCardBuildRequest, ActionCardBuildResult
from app.providers.factory import build_action_card_generator
from app.skills.fitness_video_to_action_card import FitnessVideoToActionCardSkill


router = APIRouter(tags=["action-cards"])


@lru_cache
def get_skill() -> FitnessVideoToActionCardSkill:
    return FitnessVideoToActionCardSkill(
        build_action_card_generator(get_settings())
    )


@router.post("/action-cards/build", response_model=ActionCardBuildResult)
def build_action_card(
    request: ActionCardBuildRequest,
    skill: FitnessVideoToActionCardSkill = Depends(get_skill),
) -> ActionCardBuildResult:
    return skill.execute(request)
