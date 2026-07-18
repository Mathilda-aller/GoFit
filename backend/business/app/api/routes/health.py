from fastapi import APIRouter


router = APIRouter(tags=["system"])


@router.get("/health")
def health() -> dict[str, str]:
    return {
        "status": "ok",
        "service": "business",
        "ai_center": "not_connected",
    }
