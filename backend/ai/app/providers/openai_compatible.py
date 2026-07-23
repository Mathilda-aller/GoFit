from __future__ import annotations

import base64
import json
from typing import Any

import httpx
from pydantic import ValidationError

from app.core.config import AISettings
from app.errors import SkillError
from app.media.ffmpeg import FrameSample
from app.models.action_card import (
    ActionCardBuildRequest,
    ActionCardBuildResult,
    ProviderInfo,
)
from app.models.video_workflow import OcrAnalysis, VideoAnalysis


class OpenAICompatibleProvider:
    """DashScope OpenAI-compatible provider for vision and card generation."""

    def __init__(self, settings: AISettings) -> None:
        self.settings = settings

    def analyze_frames(
        self,
        frames: list[FrameSample],
        *,
        video_title: str,
        duration_ms: int,
        request_id: str,
    ) -> VideoAnalysis:
        self.settings.require_model_api(request_id=request_id)
        content: list[dict[str, Any]] = [
            {
                "type": "text",
                "text": self._vision_prompt(video_title, duration_ms),
            }
        ]
        for frame in frames:
            encoded = base64.b64encode(frame.path.read_bytes()).decode("ascii")
            content.extend(
                [
                    {
                        "type": "text",
                        "text": f"时间 {frame.timestamp_ms}ms 的采样画面：",
                    },
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/jpeg;base64,{encoded}",
                            "detail": "low",
                        },
                    },
                ]
            )
        payload: dict[str, Any] = {
            "model": self.settings.vision_model,
            "messages": [{"role": "user", "content": content}],
            "temperature": 0,
        }
        if self.settings.use_json_response_format:
            payload["response_format"] = {"type": "json_object"}
        response = self._request(
            "POST",
            "/chat/completions",
            request_id=request_id,
            json=payload,
        )
        raw = self._chat_content(
            self._response_json(response, request_id=request_id),
            request_id=request_id,
        )
        try:
            payload = self._normalize_video_analysis(
                self._extract_json(raw),
                frames=frames,
                duration_ms=duration_ms,
            )
            return VideoAnalysis.model_validate(payload)
        except (ValidationError, ValueError, json.JSONDecodeError) as exc:
            raise SkillError(
                "VIDEO_ANALYSIS_INVALID",
                "画面理解结果不符合约定格式。",
                request_id=request_id,
            ) from exc

    def recognize_text(
        self,
        frames: list[FrameSample],
        *,
        request_id: str,
    ) -> OcrAnalysis:
        self.settings.require_model_api(request_id=request_id)
        content: list[dict[str, Any]] = [
            {
                "type": "text",
                "text": (
                    "你只负责读取健身视频采样画面中真实可见的文字。"
                    "不要推测动作名称，不要补充画面里没有的内容。"
                    "只返回包含文字的画面，timestampMs 必须原样使用输入时间。"
                    "严格返回 JSON：{\"observations\":[{\"timestampMs\":1000,"
                    "\"text\":\"画面文字\",\"confidence\":0.95}]}。"
                ),
            }
        ]
        for frame in frames:
            encoded = base64.b64encode(frame.path.read_bytes()).decode("ascii")
            content.extend(
                [
                    {
                        "type": "text",
                        "text": f"timestampMs={frame.timestamp_ms}",
                    },
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/jpeg;base64,{encoded}",
                            "detail": "high",
                        },
                    },
                ]
            )
        payload: dict[str, Any] = {
            "model": self.settings.ocr_model,
            "messages": [{"role": "user", "content": content}],
            "temperature": 0,
        }
        if self.settings.use_json_response_format:
            payload["response_format"] = {"type": "json_object"}
        response = self._request(
            "POST",
            "/chat/completions",
            request_id=request_id,
            json=payload,
        )
        raw = self._chat_content(
            self._response_json(response, request_id=request_id),
            request_id=request_id,
        )
        try:
            result = OcrAnalysis.model_validate(self._extract_json(raw))
        except (ValidationError, ValueError, json.JSONDecodeError) as exc:
            raise SkillError(
                "OCR_ANALYSIS_INVALID",
                "OCR 结果不符合约定格式。",
                request_id=request_id,
            ) from exc
        allowed_timestamps = {frame.timestamp_ms for frame in frames}
        if any(
            item.timestamp_ms not in allowed_timestamps
            for item in result.observations
        ):
            raise SkillError(
                "OCR_ANALYSIS_INVALID",
                "OCR 返回了不存在的采样画面时间。",
                request_id=request_id,
            )
        return result

    def generate(self, request: ActionCardBuildRequest) -> ActionCardBuildResult:
        self.settings.require_model_api(request_id=request.request_id)
        schema = ActionCardBuildResult.model_json_schema(by_alias=True)
        action_rule = (
            "standardActionCandidates 中唯一的动作已经由 Demo 人工确认。"
            "不要再次识别或选择动作，必须原样使用它的名称、部位、肌群和器械；"
            if len(request.standard_action_candidates) == 1
            else "动作只能从 standardActionCandidates 中选择；"
        )
        prompt = (
            "你是 GoFit 视频动作卡整理器。只使用输入中的当前视频证据，不补充常识，"
            "不读取评论或练友经验。"
            f"{action_rule}"
            "输出一张双面卡：learningSide 是完整学习正面，trainingSide 是训练速记背面。"
            "正反面必须使用同一个 CORRECT_DEMO；步骤 3 到 5 条；关键提醒最多 2 条；"
            "速记提示最多 3 条。只有存在 ERROR_DEMO 时才能生成 commonErrors。"
            "所有文字和媒体都必须引用输入里的 evidenceId。证据不足时使用 NEEDS_REVIEW，"
            "不要猜测。严格返回 JSON，不要使用 Markdown。\n\n"
            f"输入：{request.model_dump_json(by_alias=True)}\n\n"
            f"输出 JSON Schema：{json.dumps(schema, ensure_ascii=False)}"
        )
        payload: dict[str, Any] = {
            "model": self.settings.action_card_model,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0,
        }
        if self.settings.use_json_response_format:
            payload["response_format"] = {"type": "json_object"}
        response = self._request(
            "POST",
            "/chat/completions",
            request_id=request.request_id,
            json=payload,
        )
        raw = self._chat_content(
            self._response_json(response, request_id=request.request_id),
            request_id=request.request_id,
        )
        try:
            result_payload = self._extract_json(raw)
            result_payload["requestId"] = request.request_id
            result_payload["schemaVersion"] = "1.1.0"
            result_payload["provider"] = {
                "name": "dashscope",
                "version": self.settings.action_card_model,
            }
            self._apply_confirmed_action(request, result_payload)
            self._apply_confirmed_media(request, result_payload)
            result = ActionCardBuildResult.model_validate(result_payload)
            return result.model_copy(
                update={
                    "provider": ProviderInfo(
                        name="dashscope",
                        version=self.settings.action_card_model,
                    )
                }
            )
        except (ValidationError, ValueError, json.JSONDecodeError) as exc:
            raise SkillError(
                "OUTPUT_VALIDATION_FAILED",
                "模型返回的动作卡不符合约定格式。",
                request_id=request.request_id,
            ) from exc

    @staticmethod
    def _apply_confirmed_action(
        request: ActionCardBuildRequest,
        result_payload: dict[str, Any],
    ) -> None:
        """Keep manually confirmed demo identity out of generative decisions."""
        if len(request.standard_action_candidates) != 1:
            return
        candidate = request.standard_action_candidates[0]
        result_payload["standardAction"] = {
            "standardActionId": candidate.standard_action_id,
            "confidence": 1.0,
            "decision": "MATCHED",
        }
        card = result_payload.get("actionCard")
        if not isinstance(card, dict):
            raise ValueError("model result must contain actionCard")
        card.update(
            {
                "sourceVideo": request.source_video.model_dump(by_alias=True),
                "actionName": candidate.name,
                "bodyRegion": candidate.body_region,
                "primaryMuscles": candidate.primary_muscles,
                "secondaryMuscles": candidate.secondary_muscles,
                "equipment": candidate.equipment,
            }
        )

    @staticmethod
    def _apply_confirmed_media(
        request: ActionCardBuildRequest,
        result_payload: dict[str, Any],
    ) -> None:
        """Models write copy; the business-provided media selection is immutable."""
        correct = [item for item in request.media_candidates if item.kind.value == "CORRECT_DEMO"]
        errors = [item for item in request.media_candidates if item.kind.value == "ERROR_DEMO"]
        if len(correct) != 1:
            return
        card = result_payload.get("actionCard")
        if not isinstance(card, dict):
            raise ValueError("model result must contain actionCard")
        learning = card.get("learningSide")
        training = card.get("trainingSide")
        if not isinstance(learning, dict) or not isinstance(training, dict):
            raise ValueError("model result must contain both card sides")
        correct_payload = correct[0].model_dump(by_alias=True)
        learning["correctDemo"] = correct_payload
        training["loopDemo"] = correct_payload

        raw_errors = learning.get("commonErrors")
        if not isinstance(raw_errors, list):
            raw_errors = []
        if not errors:
            learning["commonErrors"] = []
            return
        if len(raw_errors) != len(errors):
            result_payload["status"] = "NEEDS_REVIEW"
            reasons = result_payload.setdefault("needsReviewReasons", [])
            if isinstance(reasons, list):
                reasons.append("模型生成的错误说明数量与人工错误片段数量不一致。")
        if len(raw_errors) < len(errors):
            return
        normalized_errors = []
        for raw_error, candidate in zip(raw_errors, errors, strict=False):
            if not isinstance(raw_error, dict):
                continue
            candidate_payload = candidate.model_dump(by_alias=True)
            normalized_errors.append({
                **raw_error,
                "errorDemo": candidate_payload,
                "evidenceIds": candidate_payload["evidenceIds"],
            })
        learning["commonErrors"] = normalized_errors

    @staticmethod
    def _normalize_video_analysis(
        payload: dict[str, Any],
        *,
        frames: list[FrameSample],
        duration_ms: int,
    ) -> dict[str, Any]:
        """Accept common model field variants while returning the strict contract."""
        raw_observations = payload.get("observations")
        if not isinstance(raw_observations, list):
            for key in ("frames", "frameObservations", "analysis"):
                value = payload.get(key)
                if isinstance(value, list):
                    raw_observations = value
                    break
        if not isinstance(raw_observations, list):
            raw_observations = []

        frame_times = sorted(frame.timestamp_ms for frame in frames)
        observations: list[dict[str, Any]] = []
        for index, raw in enumerate(raw_observations):
            if not isinstance(raw, dict):
                continue
            fallback_start = frame_times[min(index, len(frame_times) - 1)] if frame_times else 0
            start = OpenAICompatibleProvider._integer_field(
                raw, "startMs", "startTimeMs", "timestampMs", default=fallback_start
            )
            fallback_end = (
                frame_times[index + 1]
                if index + 1 < len(frame_times)
                else min(duration_ms, start + 1000)
            )
            end = OpenAICompatibleProvider._integer_field(
                raw, "endMs", "endTimeMs", default=fallback_end
            )
            start = max(0, min(start, max(duration_ms - 1, 0)))
            end = max(start + 1, min(end, duration_ms))
            description = raw.get("description") or raw.get("text") or raw.get("observation")
            if not isinstance(description, str) or not description.strip():
                continue
            confidence = raw.get("confidence")
            if isinstance(confidence, (int, float)) and not isinstance(confidence, bool):
                confidence = float(confidence)
                if 1 < confidence <= 100:
                    confidence /= 100
                confidence = max(0.0, min(confidence, 1.0))
            else:
                confidence = None
            observations.append({
                "observationId": str(raw.get("observationId") or raw.get("id") or f"frame_{index + 1:03d}"),
                "startMs": start,
                "endMs": end,
                "description": description.strip(),
                "onScreenText": raw.get("onScreenText") if isinstance(raw.get("onScreenText"), str) else None,
                "confidence": confidence,
            })

        valid_ids = {item["observationId"] for item in observations}
        proposals: list[dict[str, Any]] = []
        raw_proposals = payload.get("mediaProposals")
        if isinstance(raw_proposals, list):
            for index, raw in enumerate(raw_proposals):
                if not isinstance(raw, dict):
                    continue
                kind = str(raw.get("kind", "")).upper()
                ids = raw.get("observationIds")
                start = OpenAICompatibleProvider._integer_field(raw, "startMs", default=-1)
                end = OpenAICompatibleProvider._integer_field(raw, "endMs", default=-1)
                if kind not in {"POSTER", "CORRECT_DEMO", "ERROR_DEMO"} or not isinstance(ids, list):
                    continue
                ids = [str(item) for item in ids if str(item) in valid_ids]
                if not ids or start < 0 or end <= start or end > duration_ms:
                    continue
                proposals.append({
                    "candidateId": str(raw.get("candidateId") or f"proposal_{index + 1:03d}"),
                    "kind": kind,
                    "startMs": start,
                    "endMs": end,
                    "observationIds": ids,
                })
        return {"observations": observations, "mediaProposals": proposals}

    @staticmethod
    def _integer_field(payload: dict[str, Any], *keys: str, default: int) -> int:
        for key in keys:
            value = payload.get(key)
            if isinstance(value, (int, float)) and not isinstance(value, bool):
                return int(value)
        return default

    def _request(
        self,
        method: str,
        path: str,
        *,
        request_id: str,
        **kwargs: Any,
    ) -> httpx.Response:
        try:
            response = httpx.request(
                method,
                self.settings.api_base_url + path,
                headers={"Authorization": f"Bearer {self.settings.api_key}"},
                timeout=self.settings.model_timeout_seconds,
                **kwargs,
            )
            response.raise_for_status()
            return response
        except httpx.HTTPStatusError as exc:
            status = exc.response.status_code
            raise SkillError(
                "MODEL_API_FAILED",
                f"模型接口返回 HTTP {status}。",
                request_id=request_id,
                retryable=status == 429 or status >= 500,
            ) from exc
        except httpx.HTTPError as exc:
            raise SkillError(
                "MODEL_API_FAILED",
                "无法连接模型接口。",
                request_id=request_id,
                retryable=True,
            ) from exc

    @staticmethod
    def _response_json(response: httpx.Response, *, request_id: str) -> dict[str, Any]:
        try:
            value = response.json()
        except ValueError as exc:
            raise SkillError(
                "MODEL_API_INVALID_RESPONSE",
                "模型接口没有返回有效 JSON。",
                request_id=request_id,
            ) from exc
        if not isinstance(value, dict):
            raise SkillError(
                "MODEL_API_INVALID_RESPONSE",
                "模型接口返回格式不正确。",
                request_id=request_id,
            )
        return value

    @staticmethod
    def _chat_content(payload: dict[str, Any], *, request_id: str) -> str:
        try:
            content = payload["choices"][0]["message"]["content"]
        except (KeyError, IndexError, TypeError) as exc:
            raise SkillError(
                "MODEL_API_INVALID_RESPONSE",
                "模型接口没有返回文本结果。",
                request_id=request_id,
            ) from exc
        if isinstance(content, str):
            return content
        if isinstance(content, list):
            return "".join(
                str(item.get("text", ""))
                for item in content
                if isinstance(item, dict)
            )
        raise SkillError(
            "MODEL_API_INVALID_RESPONSE",
            "模型接口返回的文本格式不正确。",
            request_id=request_id,
        )

    @staticmethod
    def _extract_json(text: str) -> dict[str, Any]:
        cleaned = text.strip()
        if cleaned.startswith("```"):
            first_newline = cleaned.find("\n")
            cleaned = cleaned[first_newline + 1 :] if first_newline >= 0 else cleaned
        object_start = cleaned.find("{")
        if object_start < 0:
            raise json.JSONDecodeError("No JSON object found", cleaned, 0)
        value, _ = json.JSONDecoder().raw_decode(cleaned[object_start:])
        if not isinstance(value, dict):
            raise ValueError("model result must be a JSON object")
        return value

    @staticmethod
    def _vision_prompt(video_title: str, duration_ms: int) -> str:
        return (
            "你正在分析一条健身教学视频的等间隔采样画面。"
            "只描述画面中能看见的器械、身体姿态、动作阶段和文字，不补充健身常识。"
            "为每个有用观察生成 observationId、startMs、endMs、description、"
            "onScreenText 和 confidence。根据连续画面提出 POSTER、CORRECT_DEMO、"
            "ERROR_DEMO 候选区间；只有画面明确在展示错误时才能使用 ERROR_DEMO。"
            "候选使用 observationIds 绑定观察。时间必须在视频范围内。"
            "严格返回 JSON：{\"observations\":[{\"observationId\":\"obs_001\","
            "\"startMs\":0,\"endMs\":1000,\"description\":\"可见内容\","
            "\"onScreenText\":null,\"confidence\":0.9}],\"mediaProposals\":[]}。"
            "字段名、毫秒整数和枚举 POSTER/CORRECT_DEMO/ERROR_DEMO 必须完全一致。"
            f"视频标题：{video_title}；视频时长：{duration_ms}ms。"
        )
