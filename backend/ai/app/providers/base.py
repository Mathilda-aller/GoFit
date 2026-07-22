from typing import Protocol
from pathlib import Path

from app.media.ffmpeg import FrameSample
from app.models.action_card import ActionCardBuildRequest, ActionCardBuildResult
from app.models.video_workflow import OcrAnalysis, TranscriptionSegment, VideoAnalysis


class ActionCardGenerator(Protocol):
    def generate(self, request: ActionCardBuildRequest) -> ActionCardBuildResult:
        """Generate a candidate result from already-aligned evidence."""
        ...


class SpeechTranscriber(Protocol):
    def transcribe(
        self,
        audio_path: Path,
        *,
        duration_ms: int,
        request_id: str,
    ) -> list[TranscriptionSegment]:
        ...


class VideoAnalyzer(Protocol):
    def analyze_frames(
        self,
        frames: list[FrameSample],
        *,
        video_title: str,
        duration_ms: int,
        request_id: str,
    ) -> VideoAnalysis:
        ...


class FrameTextRecognizer(Protocol):
    def recognize_text(
        self,
        frames: list[FrameSample],
        *,
        request_id: str,
    ) -> OcrAnalysis:
        ...
