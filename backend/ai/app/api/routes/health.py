from fastapi import APIRouter

from app.core.config import get_settings


router = APIRouter(tags=["system"])


@router.get("/health")
def health() -> dict[str, str]:
    settings = get_settings()
    return {
        "status": "ok",
        "service": "gofit-ai",
        "provider": settings.action_card_provider,
        "modelConfigured": str(bool(settings.api_key and settings.action_card_model)).lower(),
        "fallbackEnabled": "true",
    }

