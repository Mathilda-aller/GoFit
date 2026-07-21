from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
import re
import shutil
import subprocess

from app.errors import SkillError
from app.models.action_card import MediaCandidate, MediaKind
from app.models.video_workflow import MediaArtifact


@dataclass(frozen=True)
class FrameSample:
    path: Path
    timestamp_ms: int


class FFmpegMediaProcessor:
    def __init__(self, ffmpeg_path: str, ffprobe_path: str) -> None:
        self.ffmpeg_path = ffmpeg_path
        self.ffprobe_path = ffprobe_path

    def probe_duration_ms(self, video_path: Path, *, request_id: str) -> int:
        self._require_tools(request_id)
        completed = self._run(
            [
                self.ffprobe_path,
                "-v",
                "error",
                "-show_entries",
                "format=duration",
                "-of",
                "json",
                str(video_path),
            ],
            request_id=request_id,
        )
        try:
            seconds = float(json.loads(completed.stdout)["format"]["duration"])
        except (KeyError, TypeError, ValueError, json.JSONDecodeError) as exc:
            raise SkillError(
                "VIDEO_PROBE_FAILED",
                "无法读取视频时长。",
                request_id=request_id,
            ) from exc
        return max(1, round(seconds * 1000))

    def extract_audio(
        self,
        video_path: Path,
        output_path: Path,
        *,
        request_id: str,
    ) -> Path:
        self._require_tools(request_id)
        self._run(
            [
                self.ffmpeg_path,
                "-y",
                "-i",
                str(video_path),
                "-vn",
                "-ac",
                "1",
                "-ar",
                "16000",
                "-c:a",
                "pcm_s16le",
                str(output_path),
            ],
            request_id=request_id,
        )
        return output_path

    def sample_frames(
        self,
        video_path: Path,
        output_dir: Path,
        *,
        interval_seconds: float,
        max_frames: int,
        request_id: str,
    ) -> list[FrameSample]:
        self._require_tools(request_id)
        output_dir.mkdir(parents=True, exist_ok=True)
        pattern = output_dir / "frame_%04d.jpg"
        self._run(
            [
                self.ffmpeg_path,
                "-y",
                "-i",
                str(video_path),
                "-vf",
                f"fps=1/{interval_seconds},scale=768:-2",
                "-frames:v",
                str(max_frames),
                str(pattern),
            ],
            request_id=request_id,
        )
        paths = sorted(output_dir.glob("frame_*.jpg"))
        if not paths:
            raise SkillError(
                "FRAME_EXTRACTION_FAILED",
                "没有从视频中提取到可分析画面。",
                request_id=request_id,
            )
        return [
            FrameSample(path=path, timestamp_ms=round(index * interval_seconds * 1000))
            for index, path in enumerate(paths)
        ]

    def render_candidates(
        self,
        video_path: Path,
        candidates: list[MediaCandidate],
        output_dir: Path,
        *,
        request_id: str,
    ) -> list[MediaArtifact]:
        self._require_tools(request_id)
        output_dir.mkdir(parents=True, exist_ok=True)
        artifacts: list[MediaArtifact] = []
        for candidate in candidates:
            safe_id = re.sub(r"[^a-zA-Z0-9_-]", "_", candidate.candidate_id)
            if candidate.kind == MediaKind.POSTER:
                output_path = output_dir / f"{safe_id}.jpg"
                command = [
                    self.ffmpeg_path,
                    "-y",
                    "-i",
                    str(video_path),
                    "-ss",
                    f"{candidate.start_ms / 1000:.3f}",
                    "-frames:v",
                    "1",
                    str(output_path),
                ]
            else:
                output_path = output_dir / f"{safe_id}.mp4"
                command = [
                    self.ffmpeg_path,
                    "-y",
                    "-i",
                    str(video_path),
                    "-ss",
                    f"{candidate.start_ms / 1000:.3f}",
                    "-t",
                    f"{(candidate.end_ms - candidate.start_ms) / 1000:.3f}",
                    "-an",
                    "-c:v",
                    "libx264",
                    "-pix_fmt",
                    "yuv420p",
                    "-movflags",
                    "+faststart",
                    str(output_path),
                ]
            self._run(command, request_id=request_id)
            artifacts.append(
                MediaArtifact(
                    candidateId=candidate.candidate_id,
                    kind=candidate.kind,
                    filePath=str(output_path),
                    startMs=candidate.start_ms,
                    endMs=candidate.end_ms,
                )
            )
        return artifacts

    def _require_tools(self, request_id: str) -> None:
        missing = [
            executable
            for executable in (self.ffmpeg_path, self.ffprobe_path)
            if not Path(executable).is_file() and shutil.which(executable) is None
        ]
        if missing:
            raise SkillError(
                "FFMPEG_NOT_FOUND",
                "找不到 FFmpeg 工具：" + ", ".join(missing) + "。",
                request_id=request_id,
            )

    @staticmethod
    def _run(command: list[str], *, request_id: str) -> subprocess.CompletedProcess[str]:
        try:
            return subprocess.run(
                command,
                check=True,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
            )
        except subprocess.CalledProcessError as exc:
            detail = (exc.stderr or "").strip().splitlines()
            suffix = detail[-1] if detail else "未知 FFmpeg 错误"
            raise SkillError(
                "MEDIA_PROCESSING_FAILED",
                f"视频媒体处理失败：{suffix}",
                request_id=request_id,
            ) from exc

