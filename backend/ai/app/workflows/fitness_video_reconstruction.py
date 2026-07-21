from __future__ import annotations

from collections.abc import Callable
from pathlib import Path
import re
from tempfile import TemporaryDirectory
from typing import Protocol

from app.errors import SkillError
from app.media.ffmpeg import FrameSample
from app.models.action_card import (
    ActionCardBuildRequest,
    MediaCandidate,
    MediaKind,
    TimedEvidence,
)
from app.models.video_workflow import (
    MediaArtifact,
    OcrObservation,
    TranscriptionSegment,
    VideoAnalysis,
    VideoWorkflowRequest,
    VideoWorkflowResult,
    WorkflowStage,
)
from app.providers.base import FrameTextRecognizer, SpeechTranscriber, VideoAnalyzer
from app.skills.fitness_video_to_action_card import FitnessVideoToActionCardSkill


ProgressCallback = Callable[[WorkflowStage, int, str], None]


class MediaProcessor(Protocol):
    def probe_duration_ms(self, video_path: Path, *, request_id: str) -> int: ...

    def extract_audio(
        self,
        video_path: Path,
        output_path: Path,
        *,
        request_id: str,
    ) -> Path: ...

    def sample_frames(
        self,
        video_path: Path,
        output_dir: Path,
        *,
        interval_seconds: float,
        max_frames: int,
        request_id: str,
    ) -> list[FrameSample]: ...

    def render_candidates(
        self,
        video_path: Path,
        candidates: list[MediaCandidate],
        output_dir: Path,
        *,
        request_id: str,
    ) -> list[MediaArtifact]: ...


class FitnessVideoReconstructionWorkflow:
    def __init__(
        self,
        *,
        media_processor: MediaProcessor,
        transcriber: SpeechTranscriber,
        video_analyzer: VideoAnalyzer,
        text_recognizer: FrameTextRecognizer,
        action_card_skill: FitnessVideoToActionCardSkill,
        media_output_dir: Path,
        frame_interval_seconds: float = 2.0,
        max_frames: int = 24,
    ) -> None:
        self.media_processor = media_processor
        self.transcriber = transcriber
        self.video_analyzer = video_analyzer
        self.text_recognizer = text_recognizer
        self.action_card_skill = action_card_skill
        self.media_output_dir = media_output_dir
        self.frame_interval_seconds = frame_interval_seconds
        self.max_frames = max_frames

    def execute(
        self,
        request: VideoWorkflowRequest,
        *,
        on_progress: ProgressCallback | None = None,
    ) -> VideoWorkflowResult:
        progress = on_progress or (lambda _stage, _value, _message: None)
        video_path = Path(request.video_path).expanduser().resolve()
        if not video_path.is_file():
            raise SkillError(
                "VIDEO_FILE_NOT_FOUND",
                "找不到需要处理的视频文件。",
                request_id=request.request_id,
            )

        progress(WorkflowStage.UNDERSTANDING_VIDEO, 10, "正在理解视频内容")
        duration_ms = self.media_processor.probe_duration_ms(
            video_path,
            request_id=request.request_id,
        )

        with TemporaryDirectory(prefix="gofit-video-") as temp_value:
            temp_dir = Path(temp_value)
            audio_path = self.media_processor.extract_audio(
                video_path,
                temp_dir / "audio.wav",
                request_id=request.request_id,
            )
            transcript = self.transcriber.transcribe(
                audio_path,
                duration_ms=duration_ms,
                request_id=request.request_id,
            )

            frames = self.media_processor.sample_frames(
                video_path,
                temp_dir / "frames",
                interval_seconds=self.frame_interval_seconds,
                max_frames=self.max_frames,
                request_id=request.request_id,
            )
            analysis = self.video_analyzer.analyze_frames(
                frames,
                video_title=request.source_video.title,
                duration_ms=duration_ms,
                request_id=request.request_id,
            )
            ocr_analysis = self.text_recognizer.recognize_text(
                frames,
                request_id=request.request_id,
            )

        action_card_request = self._assemble_action_card_request(
            request,
            transcript,
            analysis,
            ocr_analysis.observations,
            duration_ms=duration_ms,
        )

        progress(WorkflowStage.LOCATING_CLIPS, 65, "正在定位关键片段")
        safe_request_id = re.sub(r"[^a-zA-Z0-9_-]", "_", request.request_id)
        artifact_dir = self.media_output_dir / safe_request_id
        artifacts = self.media_processor.render_candidates(
            video_path,
            action_card_request.media_candidates,
            artifact_dir,
            request_id=request.request_id,
        )

        progress(WorkflowStage.BUILDING_CARD, 85, "正在整理动作要点")
        action_card_result = self.action_card_skill.execute(action_card_request)
        progress(WorkflowStage.COMPLETED, 100, "动作卡已生成")
        return VideoWorkflowResult(
            requestId=request.request_id,
            actionCardRequest=action_card_request,
            actionCardResult=action_card_result,
            mediaArtifacts=artifacts,
        )

    @staticmethod
    def _assemble_action_card_request(
        request: VideoWorkflowRequest,
        transcript: list[TranscriptionSegment],
        analysis: VideoAnalysis,
        ocr_observations: list[OcrObservation],
        *,
        duration_ms: int,
    ) -> ActionCardBuildRequest:
        evidence: list[TimedEvidence] = []
        for index, segment in enumerate(transcript, start=1):
            end_ms = min(segment.end_ms, duration_ms)
            if segment.start_ms >= end_ms:
                raise SkillError(
                    "ASR_TIME_RANGE_INVALID",
                    "语音识别返回了视频范围之外的时间。",
                    request_id=request.request_id,
                )
            evidence.append(
                TimedEvidence(
                    evidenceId=f"asr_{index:03d}",
                    kind="ASR",
                    startMs=segment.start_ms,
                    endMs=end_ms,
                    text=segment.text,
                    confidence=segment.confidence,
                )
            )

        observation_evidence: dict[str, list[str]] = {}
        used_evidence_ids = {item.evidence_id for item in evidence}
        for observation in analysis.observations:
            if observation.end_ms <= observation.start_ms or observation.end_ms > duration_ms:
                raise SkillError(
                    "VIDEO_ANALYSIS_INVALID",
                    "画面理解返回了视频范围之外的时间。",
                    request_id=request.request_id,
                )
            safe_id = re.sub(r"[^a-zA-Z0-9_-]", "_", observation.observation_id)
            vision_id = f"vision_{safe_id}"
            if observation.observation_id in observation_evidence or vision_id in used_evidence_ids:
                raise SkillError(
                    "VIDEO_ANALYSIS_INVALID",
                    "画面理解返回了重复的观察编号。",
                    request_id=request.request_id,
                )
            evidence.append(
                TimedEvidence(
                    evidenceId=vision_id,
                    kind="VISION",
                    startMs=observation.start_ms,
                    endMs=observation.end_ms,
                    text=observation.description,
                    confidence=observation.confidence,
                )
            )
            used_evidence_ids.add(vision_id)
            ids = [vision_id]
            if (
                not ocr_observations
                and observation.on_screen_text
                and observation.on_screen_text.strip()
            ):
                ocr_id = f"ocr_{safe_id}"
                evidence.append(
                    TimedEvidence(
                        evidenceId=ocr_id,
                        kind="OCR",
                        startMs=observation.start_ms,
                        endMs=observation.end_ms,
                        text=observation.on_screen_text.strip(),
                        confidence=observation.confidence,
                    )
                )
                used_evidence_ids.add(ocr_id)
                ids.append(ocr_id)
            observation_evidence[observation.observation_id] = ids

        for index, observation in enumerate(ocr_observations, start=1):
            if observation.timestamp_ms >= duration_ms:
                raise SkillError(
                    "OCR_ANALYSIS_INVALID",
                    "OCR 返回了视频范围之外的时间。",
                    request_id=request.request_id,
                )
            end_ms = min(duration_ms, observation.timestamp_ms + 1000)
            evidence.append(
                TimedEvidence(
                    evidenceId=f"ocr_{index:03d}",
                    kind="OCR",
                    startMs=observation.timestamp_ms,
                    endMs=end_ms,
                    text=observation.text,
                    confidence=observation.confidence,
                )
            )

        candidates: list[MediaCandidate] = []
        used_candidate_ids: set[str] = set()
        for proposal in analysis.media_proposals:
            if proposal.end_ms <= proposal.start_ms or proposal.end_ms > duration_ms:
                raise SkillError(
                    "VIDEO_ANALYSIS_INVALID",
                    "媒体候选超出了视频时间范围。",
                    request_id=request.request_id,
                )
            missing_observations = set(proposal.observation_ids) - set(
                observation_evidence
            )
            if missing_observations:
                raise SkillError(
                    "UNKNOWN_EVIDENCE_REFERENCE",
                    "媒体候选引用了不存在的画面观察。",
                    request_id=request.request_id,
                )
            if proposal.candidate_id in used_candidate_ids:
                raise SkillError(
                    "VIDEO_ANALYSIS_INVALID",
                    "画面理解返回了重复的媒体候选编号。",
                    request_id=request.request_id,
                )
            used_candidate_ids.add(proposal.candidate_id)
            evidence_ids = [
                evidence_id
                for observation_id in proposal.observation_ids
                for evidence_id in observation_evidence.get(observation_id, [])
            ]
            if not evidence_ids:
                raise SkillError(
                    "UNKNOWN_EVIDENCE_REFERENCE",
                    "媒体候选没有绑定有效的画面观察。",
                    request_id=request.request_id,
                )
            candidates.append(
                MediaCandidate(
                    candidateId=proposal.candidate_id,
                    kind=proposal.kind,
                    startMs=proposal.start_ms,
                    endMs=proposal.end_ms,
                    evidenceIds=list(dict.fromkeys(evidence_ids)),
                )
            )

        if not any(item.kind == MediaKind.CORRECT_DEMO for item in candidates):
            raise SkillError(
                "NO_CORRECT_DEMO_CANDIDATE",
                "没有找到可以循环展示的正确动作片段。",
                request_id=request.request_id,
            )

        evidence.sort(key=lambda item: (item.start_ms, item.end_ms, item.evidence_id))
        return ActionCardBuildRequest(
            requestId=request.request_id,
            sourceVideo=request.source_video,
            standardActionCandidates=request.standard_action_candidates,
            evidence=evidence,
            mediaCandidates=candidates,
        )
