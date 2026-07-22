from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
import os
from pathlib import Path

from dotenv import load_dotenv

from app.errors import SkillError


AI_ROOT = Path(__file__).resolve().parents[2]


def _read_bool(name: str, default: bool) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


@dataclass(frozen=True)
class AISettings:
    api_base_url: str
    api_key: str
    asr_api_base_url: str
    asr_model: str
    ocr_model: str
    vision_model: str
    action_card_model: str
    action_card_provider: str
    ffmpeg_path: str
    ffprobe_path: str
    media_output_dir: Path
    frame_interval_seconds: float
    max_frames: int
    model_timeout_seconds: float
    use_json_response_format: bool

    def require_model_api(self, *, request_id: str | None = None) -> None:
        missing = [
            name
            for name, value in (
                ("DASHSCOPE_API_KEY", self.api_key),
                ("GOFIT_ASR_MODEL", self.asr_model),
                ("GOFIT_OCR_MODEL", self.ocr_model),
                ("GOFIT_VISION_MODEL", self.vision_model),
                ("GOFIT_ACTION_CARD_MODEL", self.action_card_model),
            )
            if not value
        ]
        if missing:
            raise SkillError(
                "MODEL_CONFIGURATION_MISSING",
                "缺少模型配置：" + ", ".join(missing) + "。",
                request_id=request_id,
            )


@lru_cache
def get_settings() -> AISettings:
    load_dotenv(AI_ROOT / ".env", override=False)
    dashscope_base_url = os.getenv(
        "DASHSCOPE_BASE_URL",
        "https://dashscope.aliyuncs.com",
    ).rstrip("/")
    output_value = os.getenv(
        "GOFIT_MEDIA_OUTPUT_DIR",
        "../../storage/ai-generated",
    )
    output_dir = Path(output_value)
    if not output_dir.is_absolute():
        output_dir = (AI_ROOT / output_dir).resolve()

    return AISettings(
        api_base_url=os.getenv(
            "DASHSCOPE_COMPATIBLE_BASE_URL",
            f"{dashscope_base_url}/compatible-mode/v1",
        ).rstrip("/"),
        api_key=os.getenv("DASHSCOPE_API_KEY", ""),
        asr_api_base_url=os.getenv(
            "DASHSCOPE_NATIVE_BASE_URL",
            f"{dashscope_base_url}/api/v1",
        ).rstrip("/"),
        asr_model=os.getenv("GOFIT_ASR_MODEL", "qwen3-asr-flash"),
        ocr_model=os.getenv("GOFIT_OCR_MODEL", ""),
        vision_model=os.getenv("GOFIT_VISION_MODEL", ""),
        action_card_model=os.getenv("GOFIT_ACTION_CARD_MODEL", ""),
        action_card_provider=os.getenv(
            "GOFIT_ACTION_CARD_PROVIDER",
            "dashscope",
        ),
        ffmpeg_path=os.getenv("GOFIT_FFMPEG_PATH", "ffmpeg"),
        ffprobe_path=os.getenv("GOFIT_FFPROBE_PATH", "ffprobe"),
        media_output_dir=output_dir,
        frame_interval_seconds=float(
            os.getenv("GOFIT_FRAME_INTERVAL_SECONDS", "2.0")
        ),
        max_frames=int(os.getenv("GOFIT_MAX_FRAMES", "24")),
        model_timeout_seconds=float(
            os.getenv("GOFIT_MODEL_TIMEOUT_SECONDS", "120")
        ),
        use_json_response_format=_read_bool(
            "GOFIT_USE_JSON_RESPONSE_FORMAT",
            True,
        ),
    )
