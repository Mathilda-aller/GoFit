from __future__ import annotations

from dataclasses import dataclass
import json
from math import sqrt
from typing import Protocol

import httpx

from app.errors import SkillError
from app.models.peer_experience import MockPeerComment
from app.peer_experience.config import PeerExperienceSettings


@dataclass(frozen=True)
class ClusterSummary:
    method_name: str
    summary: str
    has_disagreement: bool = False


class TextEmbeddingProvider(Protocol):
    def embed(self, texts: list[str], *, request_id: str) -> list[list[float]]: ...


class PeerSummaryProvider(Protocol):
    def summarize(
        self,
        problem_tag: str,
        comments: list[MockPeerComment],
        *,
        request_id: str,
    ) -> ClusterSummary: ...


class FixedMockPeerProvider:
    """Deterministic provider for tests and the API-unavailable demo path."""

    _TOPICS = (
        ("降低重量", ("重量", "轻一点", "小重量", "太重")),
        ("由手肘带动", ("手肘", "肘部", "肘带")),
        ("避免耸肩", ("耸肩", "肩膀下沉", "肩胛下沉")),
    )

    def embed(self, texts: list[str], *, request_id: str) -> list[list[float]]:
        vectors: list[list[float]] = []
        for text in texts:
            vector = [float(any(word in text for word in words)) for _, words in self._TOPICS]
            if not any(vector):
                # A stable non-zero catch-all dimension avoids invalid cosine distances.
                vector.append(1.0)
            else:
                vector.append(0.0)
            norm = sqrt(sum(value * value for value in vector)) or 1.0
            vectors.append([value / norm for value in vector])
        return vectors

    def summarize(
        self,
        problem_tag: str,
        comments: list[MockPeerComment],
        *,
        request_id: str,
    ) -> ClusterSummary:
        joined = "\n".join(comment.text for comment in comments)
        method = next(
            (name for name, words in self._TOPICS if any(word in joined for word in words)),
            "查看原评论",
        )
        summaries = {
            "降低重量": "一些练友通过降低重量来减少其他部位抢力。",
            "由手肘带动": "一些练友尝试由手肘带动动作来寻找目标部位发力。",
            "避免耸肩": "一些练友提醒动作过程中避免耸肩。",
        }
        return ClusterSummary(method, summaries.get(method, "该组练友分享了相近的训练体感。"))


class AliyunPeerProvider:
    """OpenAI-compatible Aliyun embedding v4 and Qwen Flash provider."""

    def __init__(self, settings: PeerExperienceSettings) -> None:
        self.settings = settings

    def embed(self, texts: list[str], *, request_id: str) -> list[list[float]]:
        vectors: list[list[float]] = []
        for start in range(0, len(texts), 10):
            payload = self._post(
                "/embeddings",
                {
                    "model": self.settings.embedding_model,
                    "input": texts[start : start + 10],
                    "dimensions": self.settings.embedding_dimensions,
                },
                request_id,
            )
            try:
                rows = sorted(payload["data"], key=lambda row: row["index"])
                vectors.extend([row["embedding"] for row in rows])
            except (KeyError, TypeError) as exc:
                raise SkillError(
                    "PEER_EMBEDDING_INVALID",
                    "向量模型返回格式不正确。",
                    request_id=request_id,
                ) from exc
        if len(vectors) != len(texts):
            raise SkillError(
                "PEER_EMBEDDING_INVALID",
                "向量模型返回数量与评论数量不一致。",
                request_id=request_id,
            )
        return vectors

    def summarize(
        self,
        problem_tag: str,
        comments: list[MockPeerComment],
        *,
        request_id: str,
    ) -> ClusterSummary:
        source = [{"id": item.comment_id, "text": item.text} for item in comments]
        prompt = (
            "你是练友评论整理器。只根据输入评论生成一个不超过8字的方法名称和一句客观摘要；"
            "不得补充健身知识，不判断建议正确性。若评论包含相反建议，hasDisagreement=true。"
            "严格输出 JSON：methodName、summary、hasDisagreement。"
            f"\n问题标签：{problem_tag}\n评论：{json.dumps(source, ensure_ascii=False)}"
        )
        payload = self._post(
            "/chat/completions",
            {
                "model": self.settings.summary_model,
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0,
                "enable_thinking": False,
                "response_format": {"type": "json_object"},
            },
            request_id,
        )
        try:
            raw = payload["choices"][0]["message"]["content"]
            value = json.loads(raw)
            return ClusterSummary(
                method_name=str(value["methodName"]).strip(),
                summary=str(value["summary"]).strip(),
                has_disagreement=bool(value.get("hasDisagreement", False)),
            )
        except (KeyError, IndexError, TypeError, ValueError, json.JSONDecodeError) as exc:
            raise SkillError(
                "PEER_SUMMARY_INVALID",
                "评论摘要模型返回格式不正确。",
                request_id=request_id,
            ) from exc

    def _post(self, path: str, body: dict, request_id: str) -> dict:
        try:
            response = httpx.post(
                self.settings.api_base_url + path,
                headers={"Authorization": f"Bearer {self.settings.api_key}"},
                json=body,
                timeout=self.settings.timeout_seconds,
            )
            response.raise_for_status()
            value = response.json()
            if not isinstance(value, dict):
                raise ValueError("expected object")
            return value
        except (httpx.HTTPError, ValueError) as exc:
            raise SkillError(
                "PEER_MODEL_API_FAILED",
                "评论整理模型接口不可用。",
                request_id=request_id,
                retryable=True,
            ) from exc
