import httpx
from fastapi import APIRouter

from app.core.config import settings


router = APIRouter(tags=["system"])


@router.get("/health")
async def health() -> dict[str, str]:
    ai_center = "not_connected"
    try:
        async with httpx.AsyncClient(timeout=1.5, trust_env=False) as client:
            response = await client.get(f"{settings.ai_center_url}/internal/v1/health")
            if response.is_success:
                ai_center = "connected"
    except httpx.HTTPError:
        pass
    return {
        "status": "ok",
        "service": "business",
        "ai_center": ai_center,
    }
