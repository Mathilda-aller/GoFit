import copy
import json

import httpx
import pytest

from app.core.config import AISettings
from app.errors import SkillError
from app.media.ffmpeg import FrameSample
from app.providers.openai_compatible import OpenAICompatibleProvider


def test_extract_json_accepts_plain_and_fenced_json() -> None:
    assert OpenAICompatibleProvider._extract_json('{"ok": true}') == {"ok": True}
    assert OpenAICompatibleProvider._extract_json(
        '```json\n{"ok": true}\n```'
    ) == {"ok": True}


def test_missing_model_configuration_is_clear(tmp_path) -> None:
    settings = AISettings(
        api_base_url="https://example.test/v1",
        api_key="",
        asr_api_base_url="https://dashscope.example.test/api/v1",
        asr_model="",
        ocr_model="",
        vision_model="",
        action_card_model="",
        action_card_provider="dashscope",
        ffmpeg_path="ffmpeg",
        ffprobe_path="ffprobe",
        media_output_dir=tmp_path,
        frame_interval_seconds=2,
        max_frames=10,
        model_timeout_seconds=30,
        use_json_response_format=True,
    )

    with pytest.raises(SkillError) as caught:
        settings.require_model_api(request_id="config_test")

    assert caught.value.code == "MODEL_CONFIGURATION_MISSING"
    assert "DASHSCOPE_API_KEY" in caught.value.message


def test_confirmed_demo_action_overrides_model_identity(
    build_request,
    expected_payload: dict,
) -> None:
    payload = copy.deepcopy(expected_payload)
    payload["standardAction"] = {
        "standardActionId": "hallucinated_action",
        "confidence": 0.2,
        "decision": "NEEDS_REVIEW",
    }
    payload["actionCard"].update(
        {
            "actionName": "错误动作",
            "bodyRegion": "背部",
            "primaryMuscles": ["错误肌群"],
            "secondaryMuscles": [],
            "equipment": [],
        }
    )

    OpenAICompatibleProvider._apply_confirmed_action(build_request, payload)

    candidate = build_request.standard_action_candidates[0]
    assert payload["standardAction"] == {
        "standardActionId": candidate.standard_action_id,
        "confidence": 1.0,
        "decision": "MATCHED",
    }
    assert payload["actionCard"]["actionName"] == "哑铃侧平举"
    assert payload["actionCard"]["primaryMuscles"] == ["三角肌中束"]
    assert payload["actionCard"]["equipment"] == ["哑铃"]


def test_ocr_uses_configured_dashscope_model(tmp_path, monkeypatch) -> None:
    frame_path = tmp_path / "frame.jpg"
    frame_path.write_bytes(b"fake-jpeg")
    captured = {}
    settings = AISettings(
        api_base_url="https://dashscope.example.test/compatible-mode/v1",
        api_key="dashscope-key",
        asr_api_base_url="https://dashscope.example.test/api/v1",
        asr_model="qwen3-asr-flash",
        ocr_model="qwen3.5-ocr",
        vision_model="qwen3.6-plus",
        action_card_model="qwen-flash",
        action_card_provider="dashscope",
        ffmpeg_path="ffmpeg",
        ffprobe_path="ffprobe",
        media_output_dir=tmp_path,
        frame_interval_seconds=2,
        max_frames=10,
        model_timeout_seconds=30,
        use_json_response_format=True,
    )

    def fake_request(method, url, **kwargs):
        captured.update({"method": method, "url": url, **kwargs})
        content = json.dumps(
            {
                "observations": [
                    {
                        "timestampMs": 1000,
                        "text": "肩膀放松",
                        "confidence": 0.96,
                    }
                ]
            },
            ensure_ascii=False,
        )
        return httpx.Response(
            200,
            json={"choices": [{"message": {"content": content}}]},
            request=httpx.Request(method, url),
        )

    monkeypatch.setattr(httpx, "request", fake_request)
    result = OpenAICompatibleProvider(settings).recognize_text(
        [FrameSample(frame_path, 1000)],
        request_id="ocr_test",
    )

    assert captured["url"].endswith("/chat/completions")
    assert captured["json"]["model"] == "qwen3.5-ocr"
    assert result.observations[0].text == "肩膀放松"
