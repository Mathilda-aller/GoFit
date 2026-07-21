from __future__ import annotations

import base64
from pathlib import Path
from typing import Any

import httpx

from app.core.config import AISettings
from app.errors import SkillError
from app.models.video_workflow import TranscriptionSegment


class DashScopeAsrProvider:
    """Short-audio ASR through DashScope's synchronous multimodal endpoint."""

    def __init__(self, settings: AISettings) -> None:
        self.settings = settings

    def transcribe(
        self,
        audio_path: Path,
        *,
        duration_ms: int,
        request_id: str,
    ) -> list[TranscriptionSegment]:
        if not self.settings.api_key or not self.settings.asr_model:
            raise SkillError(
                "MODEL_CONFIGURATION_MISSING",
                "缺少 DashScope 配置：DASHSCOPE_API_KEY、GOFIT_ASR_MODEL。",
                request_id=request_id,
            )
        try:
            encoded_audio = base64.b64encode(audio_path.read_bytes()).decode("ascii")
        except OSError as exc:
            raise SkillError(
                "AUDIO_FILE_READ_FAILED",
                "无法读取待识别的音频文件。",
                request_id=request_id,
            ) from exc

        payload = {
            "model": self.settings.asr_model,
            "input": {
                "messages": [
                    {
                        "role": "user",
                        "content": [
                            {
                                "audio": (
                                    "data:audio/wav;base64," + encoded_audio
                                )
                            }
                        ],
                    }
                ]
            },
            "parameters": {
                "asr_options": {
                    "enable_itn": False,
                    "language": "zh",
                }
            },
        }
        url = (
            self.settings.asr_api_base_url
            + "/services/aigc/multimodal-generation/generation"
        )
        try:
            response = httpx.post(
                url,
                headers={
                    "Authorization": f"Bearer {self.settings.api_key}",
                    "Content-Type": "application/json",
                },
                json=payload,
                timeout=self.settings.model_timeout_seconds,
            )
            response.raise_for_status()
        except httpx.HTTPStatusError as exc:
            status = exc.response.status_code
            raise SkillError(
                "MODEL_API_FAILED",
                f"DashScope ASR 接口返回 HTTP {status}。",
                request_id=request_id,
                retryable=status == 429 or status >= 500,
            ) from exc
        except httpx.HTTPError as exc:
            raise SkillError(
                "MODEL_API_FAILED",
                "无法连接 DashScope ASR 接口。",
                request_id=request_id,
                retryable=True,
            ) from exc

        try:
            body = response.json()
        except ValueError as exc:
            raise SkillError(
                "MODEL_API_INVALID_RESPONSE",
                "DashScope ASR 接口没有返回有效 JSON。",
                request_id=request_id,
            ) from exc
        if not isinstance(body, dict):
            raise SkillError(
                "MODEL_API_INVALID_RESPONSE",
                "DashScope ASR 接口返回格式不正确。",
                request_id=request_id,
            )
        return self._segments_from_response(
            body,
            duration_ms=duration_ms,
            request_id=request_id,
        )

    @classmethod
    def _segments_from_response(
        cls,
        body: dict[str, Any],
        *,
        duration_ms: int,
        request_id: str,
    ) -> list[TranscriptionSegment]:
        segments: list[TranscriptionSegment] = []
        for raw in cls._timed_items(body):
            text = str(raw.get("text", "")).strip()
            start_value = raw.get("start_time", raw.get("begin_time"))
            end_value = raw.get("end_time")
            try:
                start_ms = int(start_value)
                end_ms = min(int(end_value), duration_ms)
            except (TypeError, ValueError):
                continue
            if not text or start_ms < 0 or end_ms <= start_ms:
                continue
            segments.append(
                TranscriptionSegment(
                    startMs=start_ms,
                    endMs=end_ms,
                    text=text,
                    confidence=cls._confidence(raw.get("confidence")),
                )
            )

        if segments:
            unique = {
                (item.start_ms, item.end_ms, item.text): item for item in segments
            }
            return sorted(
                unique.values(),
                key=lambda item: (item.start_ms, item.end_ms, item.text),
            )

        text = cls._response_text(body)
        if text:
            return [
                TranscriptionSegment(
                    startMs=0,
                    endMs=duration_ms,
                    text=text,
                )
            ]
        raise SkillError(
            "NO_SPEECH_EVIDENCE",
            "视频中没有提取到可用的口播或字幕文本。",
            request_id=request_id,
        )

    @staticmethod
    def _timed_items(value: Any) -> list[dict[str, Any]]:
        found: list[dict[str, Any]] = []
        if isinstance(value, dict):
            has_start = "start_time" in value or "begin_time" in value
            if has_start and "end_time" in value and "text" in value:
                found.append(value)
            for key, child in value.items():
                if key in {"words", "word"}:
                    continue
                found.extend(DashScopeAsrProvider._timed_items(child))
        elif isinstance(value, list):
            for child in value:
                found.extend(DashScopeAsrProvider._timed_items(child))
        return found

    @staticmethod
    def _response_text(body: dict[str, Any]) -> str:
        output = body.get("output")
        if not isinstance(output, dict):
            return ""

        choices = output.get("choices")
        if isinstance(choices, list) and choices:
            first = choices[0]
            if isinstance(first, dict):
                message = first.get("message")
                if isinstance(message, dict):
                    content = message.get("content")
                    if isinstance(content, list):
                        texts = [
                            str(item.get("text", "")).strip()
                            for item in content
                            if isinstance(item, dict) and item.get("text")
                        ]
                        if texts:
                            return "".join(texts)

        direct_text = output.get("text")
        if isinstance(direct_text, str) and direct_text.strip():
            return direct_text.strip()
        nested = output.get("output")
        if isinstance(nested, dict):
            sentence = nested.get("sentence")
            if isinstance(sentence, dict):
                text = sentence.get("text")
                if isinstance(text, str):
                    return text.strip()
        return ""

    @staticmethod
    def _confidence(value: Any) -> float | None:
        try:
            confidence = float(value)
        except (TypeError, ValueError):
            return None
        if 0 <= confidence <= 1:
            return confidence
        return None
