"""Deterministic provider for tests and offline development."""

from __future__ import annotations

import json
from typing import Any

from models.base import ChatMessage, GenerateResult, ModelProvider, ProviderHealth


class FakeProvider(ModelProvider):
    name = "fake"

    def __init__(self, scripted: dict[str, str] | None = None) -> None:
        self.scripted = scripted or {}
        self.calls: list[list[ChatMessage]] = []

    async def health(self) -> ProviderHealth:
        return ProviderHealth(online=True, provider=self.name, models=["fake-model"], detail="ok")

    async def generate(
        self,
        messages: list[ChatMessage],
        *,
        model: str | None = None,
        temperature: float = 0.4,
        response_format: str | None = None,
    ) -> GenerateResult:
        self.calls.append(messages)
        blob = "\n".join(message.content for message in messages)
        key = self._match_key(blob)
        if key and key in self.scripted:
            text = self.scripted[key]
        elif "JSON" in blob.upper() and "overall_score" in blob:
            text = json.dumps(
                {
                    "overall_score": 72,
                    "hook_score": 70,
                    "originality_score": 75,
                    "specificity_score": 68,
                    "discussion_score": 71,
                    "ai_pattern_score": 20,
                    "problems": [],
                    "improvements": ["Add one concrete example"],
                }
            )
        elif "JSON" in blob.upper() and "originality" in blob:
            text = json.dumps(
                {
                    "originality": 70,
                    "human_quality": 75,
                    "engagement_probability": 68,
                    "evidence_quality": 60,
                    "ai_pattern_score": 25,
                    "issues": [],
                }
            )
        else:
            text = (
                "I spent time testing this workflow, and one pattern stood out.\n\n"
                "Specific systems beat generic advice.\n\n"
                "What have you tested recently?"
            )
        return GenerateResult(text=text, model=model or "fake-model", provider=self.name)

    def _match_key(self, blob: str) -> str | None:
        for key in self.scripted:
            if key.lower() in blob.lower():
                return key
        return None
