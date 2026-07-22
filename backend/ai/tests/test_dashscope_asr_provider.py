import base64

import httpx

from app.core.config import AISettings
from app.providers.dashscope_asr import DashScopeAsrProvider


def make_settings(tmp_path) -> AISettings:
    return AISettings(
        api_base_url="https://dashscope.example.test/compatible-mode/v1",
        api_key="dashscope-key",
        asr_api_base_url="https://dashscope.example.test/api/v1",
        asr_model="qwen3-asr-flash",
        ocr_model="qwen3.5-ocr",
        vision_model="qwen-vl-model",
        action_card_model="qwen-card-model",
        action_card_provider="dashscope",
        ffmpeg_path="ffmpeg",
        ffprobe_path="ffprobe",
        media_output_dir=tmp_path,
        frame_interval_seconds=2,
        max_frames=10,
        model_timeout_seconds=30,
        use_json_response_format=True,
    )


def test_dashscope_asr_sends_data_uri_and_reads_timed_segments(
    tmp_path,
    monkeypatch,
) -> None:
    audio_path = tmp_path / "audio.wav"
    audio_path.write_bytes(b"fake-wave")
    captured = {}

    def fake_post(url, *, headers, json, timeout):
        captured.update(
            {"url": url, "headers": headers, "json": json, "timeout": timeout}
        )
        return httpx.Response(
            200,
            json={
                "output": {
                    "sentences": [
                        {
                            "begin_time": 450,
                            "end_time": 1530,
                            "text": "保持肩膀放松。",
                        }
                    ]
                }
            },
            request=httpx.Request("POST", url),
        )

    monkeypatch.setattr(httpx, "post", fake_post)
    segments = DashScopeAsrProvider(make_settings(tmp_path)).transcribe(
        audio_path,
        duration_ms=2499,
        request_id="asr_test",
    )

    assert captured["url"].endswith(
        "/services/aigc/multimodal-generation/generation"
    )
    assert captured["headers"]["Authorization"] == "Bearer dashscope-key"
    assert captured["json"]["model"] == "qwen3-asr-flash"
    audio_uri = captured["json"]["input"]["messages"][0]["content"][0]["audio"]
    assert audio_uri.startswith("data:audio/wav;base64,")
    assert base64.b64decode(audio_uri.split(",", 1)[1]) == b"fake-wave"
    assert segments[0].start_ms == 450
    assert segments[0].end_ms == 1530


def test_dashscope_asr_falls_back_to_full_duration_text(tmp_path, monkeypatch) -> None:
    audio_path = tmp_path / "audio.wav"
    audio_path.write_bytes(b"fake-wave")

    def fake_post(url, **_kwargs):
        return httpx.Response(
            200,
            json={
                "output": {
                    "choices": [
                        {
                            "message": {
                                "content": [{"text": "完整口播文本。"}]
                            }
                        }
                    ]
                }
            },
            request=httpx.Request("POST", url),
        )

    monkeypatch.setattr(httpx, "post", fake_post)
    segments = DashScopeAsrProvider(make_settings(tmp_path)).transcribe(
        audio_path,
        duration_ms=3000,
        request_id="asr_fallback",
    )

    assert segments[0].start_ms == 0
    assert segments[0].end_ms == 3000
    assert segments[0].text == "完整口播文本。"
