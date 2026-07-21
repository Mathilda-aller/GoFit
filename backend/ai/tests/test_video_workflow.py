from __future__ import annotations

from pathlib import Path

import pytest

from app.errors import SkillError
from app.media.ffmpeg import FFmpegMediaProcessor, FrameSample
from app.models.action_card import (
    ActionCardBuildRequest,
    ActionCardBuildResult,
    MediaCandidate,
)
from app.models.video_workflow import (
    FrameObservation,
    MediaArtifact,
    MediaProposal,
    OcrAnalysis,
    OcrObservation,
    TranscriptionSegment,
    VideoAnalysis,
    VideoWorkflowRequest,
    WorkflowStage,
)
from app.skills.fitness_video_to_action_card import FitnessVideoToActionCardSkill
from app.workflows.fitness_video_reconstruction import FitnessVideoReconstructionWorkflow


class FakeMediaProcessor:
    def probe_duration_ms(self, _video_path: Path, *, request_id: str) -> int:
        return 10_000

    def extract_audio(
        self,
        _video_path: Path,
        output_path: Path,
        *,
        request_id: str,
    ) -> Path:
        return output_path

    def sample_frames(
        self,
        _video_path: Path,
        output_dir: Path,
        *,
        interval_seconds: float,
        max_frames: int,
        request_id: str,
    ) -> list[FrameSample]:
        return [
            FrameSample(output_dir / "frame_0001.jpg", 1000),
            FrameSample(output_dir / "frame_0002.jpg", 4000),
        ]

    def render_candidates(
        self,
        _video_path: Path,
        candidates: list[MediaCandidate],
        output_dir: Path,
        *,
        request_id: str,
    ) -> list[MediaArtifact]:
        return [
            MediaArtifact(
                candidateId=item.candidate_id,
                kind=item.kind,
                filePath=str(output_dir / f"{item.candidate_id}.mp4"),
                startMs=item.start_ms,
                endMs=item.end_ms,
            )
            for item in candidates
        ]


class FakeTranscriber:
    def transcribe(
        self,
        _audio_path: Path,
        *,
        duration_ms: int,
        request_id: str,
    ) -> list[TranscriptionSegment]:
        return [
            TranscriptionSegment(
                startMs=0,
                endMs=3000,
                text="站稳后，用肘部带动手臂抬起。",
                confidence=0.98,
            )
        ]


class FakeVideoAnalyzer:
    def __init__(self, include_demo: bool = True) -> None:
        self.include_demo = include_demo

    def analyze_frames(
        self,
        _frames: list[FrameSample],
        *,
        video_title: str,
        duration_ms: int,
        request_id: str,
    ) -> VideoAnalysis:
        proposals = []
        if self.include_demo:
            proposals.append(
                MediaProposal(
                    candidateId="correct_demo",
                    kind="CORRECT_DEMO",
                    startMs=1000,
                    endMs=8000,
                    observationIds=["setup", "raise"],
                )
            )
        return VideoAnalysis(
            observations=[
                FrameObservation(
                    observationId="setup",
                    startMs=1000,
                    endMs=4000,
                    description="人物站稳并放松肩膀。",
                    onScreenText="肩膀放松",
                    confidence=0.95,
                ),
                FrameObservation(
                    observationId="raise",
                    startMs=4000,
                    endMs=8000,
                    description="手臂向两侧抬起后缓慢放下。",
                    confidence=0.96,
                ),
            ],
            mediaProposals=proposals,
        )


class FakeTextRecognizer:
    def recognize_text(
        self,
        _frames: list[FrameSample],
        *,
        request_id: str,
    ) -> OcrAnalysis:
        return OcrAnalysis(
            observations=[
                OcrObservation(
                    timestampMs=1000,
                    text="肩膀放松",
                    confidence=0.97,
                )
            ]
        )


class GroundedGenerator:
    def generate(self, request: ActionCardBuildRequest) -> ActionCardBuildResult:
        action = request.standard_action_candidates[0]
        demo = next(
            item for item in request.media_candidates if item.kind == "CORRECT_DEMO"
        )
        references = [request.evidence[index].evidence_id for index in range(3)]
        demo_payload = {
            "kind": demo.kind,
            "candidateId": demo.candidate_id,
            "startMs": demo.start_ms,
            "endMs": demo.end_ms,
            "evidenceIds": demo.evidence_ids,
        }
        return ActionCardBuildResult.model_validate(
            {
                "schemaVersion": "1.1.0",
                "requestId": request.request_id,
                "status": "READY",
                "standardAction": {
                    "standardActionId": action.standard_action_id,
                    "confidence": 0.95,
                    "decision": "MATCHED",
                },
                "actionCard": {
                    "sourceVideo": request.source_video.model_dump(by_alias=True),
                    "actionName": action.name,
                    "bodyRegion": action.body_region,
                    "primaryMuscles": action.primary_muscles,
                    "secondaryMuscles": action.secondary_muscles,
                    "equipment": action.equipment,
                    "learningSide": {
                        "correctDemo": demo_payload,
                        "steps": [
                            {
                                "order": index,
                                "instruction": f"测试步骤 {index}",
                                "startMs": 1000,
                                "endMs": 4000,
                                "evidenceIds": [references[index - 1]],
                            }
                            for index in range(1, 4)
                        ],
                        "keyReminders": [
                            {"text": "肩膀放松", "evidenceIds": [references[0]]}
                        ],
                        "commonErrors": [],
                    },
                    "trainingSide": {
                        "loopDemo": demo_payload,
                        "quickCue": {
                            "text": "站稳 → 肘带动 → 慢放",
                            "evidenceIds": references,
                        },
                        "quickTips": [
                            {"text": "肩膀放松", "evidenceIds": [references[0]]}
                        ],
                    },
                },
                "warnings": [],
                "needsReviewReasons": [],
                "provider": {"name": "test", "version": "1"},
            }
        )


def make_request(video_path: Path) -> VideoWorkflowRequest:
    return VideoWorkflowRequest.model_validate(
        {
            "requestId": "workflow_test_001",
            "sourceVideo": {
                "videoId": "video_test_001",
                "title": "测试侧平举视频",
                "creatorName": "测试教练",
                "sourceUrl": "https://example.test/video",
            },
            "videoPath": str(video_path),
            "standardActionCandidates": [
                {
                    "standardActionId": "action_test_001",
                    "name": "哑铃侧平举",
                    "aliases": ["侧平举"],
                    "bodyRegion": "肩部",
                    "primaryMuscles": ["三角肌中束"],
                    "secondaryMuscles": [],
                    "equipment": ["哑铃"],
                }
            ],
        }
    )


def make_workflow(tmp_path: Path, *, include_demo: bool = True):
    return FitnessVideoReconstructionWorkflow(
        media_processor=FakeMediaProcessor(),
        transcriber=FakeTranscriber(),
        video_analyzer=FakeVideoAnalyzer(include_demo=include_demo),
        text_recognizer=FakeTextRecognizer(),
        action_card_skill=FitnessVideoToActionCardSkill(GroundedGenerator()),
        media_output_dir=tmp_path / "generated",
    )


def test_workflow_builds_aligned_input_and_two_sided_card(tmp_path: Path) -> None:
    video_path = tmp_path / "video.mp4"
    video_path.write_bytes(b"fake video")
    stages: list[WorkflowStage] = []

    result = make_workflow(tmp_path).execute(
        make_request(video_path),
        on_progress=lambda stage, _progress, _message: stages.append(stage),
    )

    kinds = {item.kind for item in result.action_card_request.evidence}
    assert kinds == {"ASR", "OCR", "VISION"}
    assert result.action_card_result.action_card.learning_side.correct_demo is not None
    assert result.action_card_result.action_card.training_side.loop_demo is not None
    assert result.media_artifacts[0].candidate_id == "correct_demo"
    assert stages == [
        WorkflowStage.UNDERSTANDING_VIDEO,
        WorkflowStage.LOCATING_CLIPS,
        WorkflowStage.BUILDING_CARD,
        WorkflowStage.COMPLETED,
    ]


def test_workflow_rejects_video_without_correct_demo(tmp_path: Path) -> None:
    video_path = tmp_path / "video.mp4"
    video_path.write_bytes(b"fake video")

    with pytest.raises(SkillError) as caught:
        make_workflow(tmp_path, include_demo=False).execute(make_request(video_path))

    assert caught.value.code == "NO_CORRECT_DEMO_CANDIDATE"


def test_ffmpeg_missing_has_clear_error(tmp_path: Path) -> None:
    processor = FFmpegMediaProcessor(
        "definitely-missing-ffmpeg",
        "definitely-missing-ffprobe",
    )

    with pytest.raises(SkillError) as caught:
        processor.probe_duration_ms(tmp_path / "video.mp4", request_id="test")

    assert caught.value.code == "FFMPEG_NOT_FOUND"
