from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
from pathlib import Path
from typing import Any

from fastapi import HTTPException

from app.core.storage import curated_storage_dir, resolve_curated_path, resolve_video_path


ACTION_TO_EXERCISE = {
    "action_lateral_raise": "exercise_lateral_raise",
    "action_front_raise": "exercise_front_raise",
    "action_reverse_fly": "exercise_reverse_fly",
    "action_shoulder_press": "exercise_shoulder_press",
    "action_face_pull": "exercise_face_pull",
    "action_lat_pulldown": "exercise_lat_pulldown",
    "action_seated_cable_row": "exercise_seated_row",
    "action_one_arm_dumbbell_row": "exercise_one_arm_row",
    "action_chest_supported_row": "exercise_chest_supported_row",
    "action_straight_arm_pulldown": "exercise_straight_arm_pulldown",
}


@dataclass(frozen=True)
class CuratedClip:
    candidate_id: str
    file_path: Path
    relative_path: str
    source_start_ms: int
    source_end_ms: int

    def ai_payload(self) -> dict[str, Any]:
        return {
            "candidateId": self.candidate_id,
            "filePath": str(self.file_path),
            "sourceStartMs": self.source_start_ms,
            "sourceEndMs": self.source_end_ms,
        }


@dataclass(frozen=True)
class CuratedManifest:
    path: Path
    standard_action_id: str
    action_name: str
    declared_video_id: str
    source_file_name: str
    title: str
    creator_name: str
    source_url: str
    correct_clip: CuratedClip
    error_clips: tuple[CuratedClip, ...]


def _bad(message: str) -> HTTPException:
    return HTTPException(status_code=422, detail=message)


def _clip(raw: Any, *, manifest_path: Path) -> CuratedClip:
    if not isinstance(raw, dict):
        raise _bad(f"Invalid clip entry in {manifest_path.name}.")
    candidate_id = raw.get("candidateId")
    file_value = raw.get("file")
    start_ms = raw.get("sourceStartMs")
    end_ms = raw.get("sourceEndMs")
    if not isinstance(candidate_id, str) or not candidate_id.strip():
        raise _bad("Every curated clip requires a candidateId.")
    if not isinstance(file_value, str):
        raise _bad(f"Curated clip {candidate_id} requires a file.")
    if not isinstance(start_ms, int) or not isinstance(end_ms, int) or start_ms < 0 or end_ms <= start_ms:
        raise _bad(f"Curated clip {candidate_id} has an invalid source time range.")
    prefix = "storage/curated-clips/"
    normalized = file_value.replace("\\", "/")
    if not normalized.startswith(prefix):
        raise _bad(f"Curated clip {candidate_id} must be inside storage/curated-clips.")
    relative = normalized.removeprefix(prefix)
    return CuratedClip(
        candidate_id=candidate_id,
        file_path=resolve_curated_path(relative),
        relative_path=relative,
        source_start_ms=start_ms,
        source_end_ms=end_ms,
    )


def load_manifest_for_video(asset_file_name: str) -> CuratedManifest:
    source_path = resolve_video_path(asset_file_name)
    matches: list[tuple[Path, dict[str, Any]]] = []
    for path in curated_storage_dir().glob("*/manifest.json"):
        try:
            raw = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            raise _bad(f"Cannot read curated manifest {path.name}: {exc}") from exc
        source = raw.get("sourceVideo") if isinstance(raw, dict) else None
        file_value = source.get("file") if isinstance(source, dict) else None
        if isinstance(file_value, str) and Path(file_value).name == source_path.name:
            matches.append((path, raw))
    if not matches:
        raise _bad(f"No curated manifest found for {asset_file_name}.")
    if len(matches) > 1:
        raise _bad(f"Multiple curated manifests reference {asset_file_name}.")

    path, raw = matches[0]
    action_id = raw.get("standardActionId")
    if action_id not in ACTION_TO_EXERCISE:
        raise _bad("standardActionId is not in the ten-action whitelist.")
    action_name = raw.get("actionName")
    source = raw.get("sourceVideo")
    if not isinstance(action_name, str) or not isinstance(source, dict):
        raise _bad("Manifest actionName and sourceVideo are required.")
    source_file = source.get("file")
    if not isinstance(source_file, str) or source_file.replace("\\", "/") != f"storage/videos/{source_path.name}":
        raise _bad("Manifest source video must be inside storage/videos.")
    correct = raw.get("correctClips")
    if not isinstance(correct, list) or len(correct) != 1:
        raise _bad("Manifest must contain exactly one primary correct clip.")
    errors = raw.get("errorClips", [])
    if not isinstance(errors, list):
        raise _bad("Manifest errorClips must be an array.")
    correct_clip = _clip(correct[0], manifest_path=path)
    error_clips = tuple(_clip(item, manifest_path=path) for item in errors)
    ids = [correct_clip.candidate_id, *(item.candidate_id for item in error_clips)]
    if len(ids) != len(set(ids)):
        raise _bad("Curated candidateIds must be unique within a manifest.")

    required_source = ("videoId", "title", "creatorName", "sourceUrl")
    if any(not isinstance(source.get(key), str) or not source[key].strip() for key in required_source):
        raise _bad("Manifest sourceVideo metadata is incomplete.")
    return CuratedManifest(
        path=path,
        standard_action_id=action_id,
        action_name=action_name,
        declared_video_id=source["videoId"],
        source_file_name=source_path.name,
        title=source["title"],
        creator_name=source["creatorName"],
        source_url=source["sourceUrl"],
        correct_clip=correct_clip,
        error_clips=error_clips,
    )


def fingerprint_video(manifest: CuratedManifest) -> str:
    digest = hashlib.sha256()
    with resolve_video_path(manifest.source_file_name).open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    digest.update(b"\0")
    digest.update(manifest.standard_action_id.encode("utf-8"))
    return f"video_{digest.hexdigest()[:24]}"


def load_manifest_for_fingerprint(video_id: str) -> CuratedManifest:
    for path in curated_storage_dir().glob("*/manifest.json"):
        try:
            raw = json.loads(path.read_text(encoding="utf-8"))
            source = raw.get("sourceVideo", {})
            file_value = source.get("file")
            if not isinstance(file_value, str):
                continue
            manifest = load_manifest_for_video(Path(file_value).name)
            if fingerprint_video(manifest) == video_id:
                return manifest
        except HTTPException:
            continue
    raise _bad(f"No curated manifest found for video identity {video_id}.")
