from fastapi import APIRouter, Depends

from app.models.action_card import ActionCardBuildRequest, ActionCardBuildResult
from app.providers.fake import FixedFixtureActionCardGenerator
from app.skills.fitness_video_to_action_card import FitnessVideoToActionCardSkill


router = APIRouter(tags=["action-cards"])
_skill = FitnessVideoToActionCardSkill(FixedFixtureActionCardGenerator())


def get_skill() -> FitnessVideoToActionCardSkill:
    return _skill


@router.post("/action-cards/build", response_model=ActionCardBuildResult)
def build_action_card(
    request: ActionCardBuildRequest,
    skill: FitnessVideoToActionCardSkill = Depends(get_skill),
) -> ActionCardBuildResult:
    return skill.execute(request)

