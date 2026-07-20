import json
from pathlib import Path

from fastapi import APIRouter, Depends

from app.models.peer_experience import (
    PeerExperienceDigestRequest,
    PeerExperienceDigestResult,
    PeerExperienceMatchRequest,
    PeerExperienceMatchResult,
)
from app.peer_experience.providers import AliyunPeerProvider, FixedMockPeerProvider
from app.peer_experience.config import get_peer_experience_settings
from app.peer_experience.service import PeerExperienceService


router = APIRouter(tags=["peer-experiences"])
_FALLBACK_PATH = (
    Path(__file__).resolve().parents[3]
    / "fixtures"
    / "peer_experience"
    / "expected-digest.json"
)


def _fallback_results() -> dict[str, PeerExperienceDigestResult]:
    value = PeerExperienceDigestResult.model_validate(
        json.loads(_FALLBACK_PATH.read_text(encoding="utf-8"))
    )
    return {value.standard_action_id: value}


def get_peer_experience_service() -> PeerExperienceService:
    settings = get_peer_experience_settings()
    if settings.provider == "aliyun":
        provider = AliyunPeerProvider(settings)
        return PeerExperienceService(
            provider,
            provider,
            provider_mode="aliyun-live",
            fallback_results=_fallback_results(),
        )
    provider = FixedMockPeerProvider()
    return PeerExperienceService(provider, provider, provider_mode="fixed-mock")


@router.post("/peer-experiences/digest", response_model=PeerExperienceDigestResult)
def digest_peer_experiences(
    request: PeerExperienceDigestRequest,
    service: PeerExperienceService = Depends(get_peer_experience_service),
) -> PeerExperienceDigestResult:
    return service.digest(request)


@router.post("/peer-experiences/match", response_model=PeerExperienceMatchResult)
def match_peer_experiences(
    request: PeerExperienceMatchRequest,
    service: PeerExperienceService = Depends(get_peer_experience_service),
) -> PeerExperienceMatchResult:
    return service.match(request)
