from __future__ import annotations

from collections.abc import Iterable

from app.errors import SkillError
from app.models.action_card import (
    ActionCardBuildRequest,
    ActionCardBuildResult,
    BuildStatus,
    MediaKind,
    MediaSelection,
)
from app.providers.base import ActionCardGenerator


class FitnessVideoToActionCardSkill:
    """Build and validate an evidence-grounded action card."""

    def __init__(self, generator: ActionCardGenerator) -> None:
        self.generator = generator

    def execute(self, request: ActionCardBuildRequest) -> ActionCardBuildResult:
        if not request.evidence:
            raise SkillError(
                "NO_EVIDENCE",
                "缺少生成动作卡所需的来源证据。",
                request_id=request.request_id,
            )
        if not request.standard_action_candidates:
            raise SkillError(
                "NO_STANDARD_ACTION_CANDIDATES",
                "缺少业务后端提供的标准动作候选。",
                request_id=request.request_id,
            )
        for item in request.evidence:
            if item.end_ms <= item.start_ms:
                raise SkillError(
                    "INVALID_EVIDENCE_RANGE",
                    "证据的结束时间必须晚于开始时间。",
                    request_id=request.request_id,
                )

        evidence_ids = {item.evidence_id for item in request.evidence}
        unknown_input_references = {
            evidence_id
            for candidate in request.media_candidates
            for evidence_id in candidate.evidence_ids
            if evidence_id not in evidence_ids
        }
        if unknown_input_references:
            raise SkillError(
                "UNKNOWN_EVIDENCE_REFERENCE",
                "媒体候选引用了不存在的证据："
                f"{', '.join(sorted(unknown_input_references))}。",
                request_id=request.request_id,
            )

        result = self.generator.generate(request)
        self._validate_result(request, result)
        return result

    def _validate_result(
        self,
        request: ActionCardBuildRequest,
        result: ActionCardBuildResult,
    ) -> None:
        evidence_ids = {item.evidence_id for item in request.evidence}
        candidates_by_id = {
            candidate.standard_action_id: candidate
            for candidate in request.standard_action_candidates
        }

        if result.request_id != request.request_id:
            self._invalid_output(request, "输出的 requestId 与输入不一致。")
        if result.action_card.source_video != request.source_video:
            self._invalid_output(request, "输出引用了其他来源视频。")
        selected_action = candidates_by_id.get(
            result.standard_action.standard_action_id
        )
        if selected_action is None:
            self._invalid_output(request, "输出选择了候选列表之外的标准动作。")

        card = result.action_card
        if (
            card.action_name != selected_action.name
            or card.body_region != selected_action.body_region
            or card.primary_muscles != selected_action.primary_muscles
            or card.secondary_muscles != selected_action.secondary_muscles
            or card.equipment != selected_action.equipment
        ):
            self._invalid_output(request, "动作身份与选中的标准动作不一致。")

        correct_demo = card.learning_side.correct_demo
        loop_demo = card.training_side.loop_demo
        if result.status == BuildStatus.READY and (
            correct_demo is None or loop_demo is None
        ):
            self._invalid_output(request, "READY 动作卡的正反面都必须包含示范片段。")
        if correct_demo is not None and correct_demo.kind != MediaKind.CORRECT_DEMO:
            self._invalid_output(request, "正确示范必须来自 CORRECT_DEMO 候选区间。")
        if loop_demo is not None and loop_demo.kind != MediaKind.CORRECT_DEMO:
            self._invalid_output(request, "训练背面的循环片段必须是正确示范。")
        if correct_demo != loop_demo:
            self._invalid_output(request, "动作卡正反面必须使用同一段正确示范。")

        unknown = set(self._all_evidence_references(result)) - evidence_ids
        if unknown:
            raise SkillError(
                "UNKNOWN_EVIDENCE_REFERENCE",
                f"输出引用了不存在的证据：{', '.join(sorted(unknown))}。",
                request_id=request.request_id,
            )

        media_by_id = {item.candidate_id: item for item in request.media_candidates}
        for selected in self._selected_media(result):
            source = media_by_id.get(selected.candidate_id)
            if source is None:
                self._invalid_output(request, "输出选择了不存在的媒体候选区间。")
            if (
                selected.kind != source.kind
                or selected.start_ms != source.start_ms
                or selected.end_ms != source.end_ms
                or set(selected.evidence_ids) != set(source.evidence_ids)
            ):
                self._invalid_output(request, "媒体选择与输入候选区间不一致。")

        for common_error in card.learning_side.common_errors:
            if common_error.error_demo.kind != MediaKind.ERROR_DEMO:
                self._invalid_output(
                    request,
                    "常见错误必须包含原视频的 ERROR_DEMO 片段。",
                )
            if not set(common_error.evidence_ids).issubset(
                set(common_error.error_demo.evidence_ids)
            ):
                self._invalid_output(request, "常见错误没有完全绑定错误示范证据。")

    @staticmethod
    def _all_evidence_references(
        result: ActionCardBuildResult,
    ) -> Iterable[str]:
        card = result.action_card
        for step in card.learning_side.steps:
            yield from step.evidence_ids
        for reminder in card.learning_side.key_reminders:
            yield from reminder.evidence_ids
        yield from card.training_side.quick_cue.evidence_ids
        for tip in card.training_side.quick_tips:
            yield from tip.evidence_ids
        for common_error in card.learning_side.common_errors:
            yield from common_error.evidence_ids
            yield from common_error.error_demo.evidence_ids
        if card.learning_side.correct_demo is not None:
            yield from card.learning_side.correct_demo.evidence_ids
        if card.training_side.loop_demo is not None:
            yield from card.training_side.loop_demo.evidence_ids

    @staticmethod
    def _selected_media(
        result: ActionCardBuildResult,
    ) -> Iterable[MediaSelection]:
        card = result.action_card
        if card.learning_side.correct_demo is not None:
            yield card.learning_side.correct_demo
        if card.training_side.loop_demo is not None:
            yield card.training_side.loop_demo
        for common_error in card.learning_side.common_errors:
            yield common_error.error_demo

    @staticmethod
    def _invalid_output(request: ActionCardBuildRequest, message: str) -> None:
        raise SkillError(
            "OUTPUT_VALIDATION_FAILED",
            message,
            request_id=request.request_id,
        )
