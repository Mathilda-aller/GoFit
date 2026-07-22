from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
import os
from pathlib import Path

from dotenv import load_dotenv


AI_ROOT = Path(__file__).resolve().parents[2]


@dataclass(frozen=True)
class PeerExperienceSettings:
    provider: str
    api_base_url: str
    api_key: str
    embedding_model: str
    embedding_dimensions: int
    summary_model: str
    timeout_seconds: float


@lru_cache
def get_peer_experience_settings() -> PeerExperienceSettings:
    load_dotenv(AI_ROOT / ".env", override=False)
    dashscope_base_url = os.getenv(
        "DASHSCOPE_BASE_URL",
        "https://dashscope.aliyuncs.com",
    ).rstrip("/")
    return PeerExperienceSettings(
        provider=os.getenv("GOFIT_PEER_PROVIDER", "aliyun"),
        api_base_url=os.getenv(
            "GOFIT_PEER_API_BASE_URL",
            f"{dashscope_base_url}/compatible-mode/v1",
        ).rstrip("/"),
        api_key=(
            os.getenv("GOFIT_PEER_API_KEY")
            or os.getenv("DASHSCOPE_API_KEY", "")
        ),
        embedding_model=os.getenv(
            "GOFIT_PEER_EMBEDDING_MODEL",
            "text-embedding-v4",
        ),
        embedding_dimensions=int(
            os.getenv("GOFIT_PEER_EMBEDDING_DIMENSIONS", "1024")
        ),
        summary_model=os.getenv("GOFIT_PEER_SUMMARY_MODEL", "qwen-flash"),
        timeout_seconds=float(os.getenv("GOFIT_MODEL_TIMEOUT_SECONDS", "120")),
    )
