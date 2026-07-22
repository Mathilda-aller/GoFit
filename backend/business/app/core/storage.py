from __future__ import annotations

from pathlib import Path

from fastapi import HTTPException

from app.core.config import settings


BUSINESS_ROOT = Path(__file__).resolve().parents[2]
ALLOWED_VIDEO_SUFFIXES = {".mp4", ".mov", ".m4v", ".webm"}


def storage_root() -> Path:
    configured = Path(settings.storage_dir).expanduser()
    if not configured.is_absolute():
        configured = BUSINESS_ROOT / configured
    return configured.resolve()


def video_storage_dir() -> Path:
    path = storage_root() / "videos"
    path.mkdir(parents=True, exist_ok=True)
    return path


def resolve_video_path(file_name: str, *, must_exist: bool = True) -> Path:
    safe_name = Path(file_name).name
    if safe_name != file_name or Path(safe_name).suffix.lower() not in ALLOWED_VIDEO_SUFFIXES:
        raise HTTPException(status_code=400, detail="Invalid video file name.")

    video_dir = video_storage_dir()
    path = (video_dir / safe_name).resolve()
    if path.parent != video_dir:
        raise HTTPException(status_code=400, detail="Invalid video file path.")
    if must_exist and not path.is_file():
        raise HTTPException(status_code=404, detail="Video file not found in storage/videos.")
    return path
