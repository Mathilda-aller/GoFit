from app.core.config import AISettings
from app.errors import SkillError
from app.providers.base import ActionCardGenerator
from app.providers.fake import FixedFixtureActionCardGenerator
from app.providers.openai_compatible import OpenAICompatibleProvider


def build_action_card_generator(settings: AISettings) -> ActionCardGenerator:
    if settings.action_card_provider == "fixed-fixture":
        return FixedFixtureActionCardGenerator()
    if settings.action_card_provider in {"dashscope", "openai-compatible"}:
        settings.require_model_api()
        return OpenAICompatibleProvider(settings)
    raise SkillError(
        "MODEL_CONFIGURATION_INVALID",
        "GOFIT_ACTION_CARD_PROVIDER 只能是 fixed-fixture 或 dashscope。",
    )
