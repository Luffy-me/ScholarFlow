"""Deterministic provider for tests and offline development."""

from __future__ import annotations

import json
import re
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
        elif "JSON" in blob.upper() and ("key_findings" in blob.lower() or "research briefing" in blob.lower() or "Produce a brief research" in blob):
            text = json.dumps(
                {
                    "topic": "local AI",
                    "key_findings": ["Evaluation loops matter more than model size", "Specific systems beat slogans"],
                    "sources": [],
                    "open_questions": ["What constraint limits your workflow?"],
                }
            )
        elif "JSON" in blob.upper() and (
            "trend analyst" in blob.lower()
            or "trend_level" in blob.lower()
            or "Produce trend analysis" in blob
        ):
            text = json.dumps(
                {
                    "topic": "local AI",
                    "trend_level": "rising",
                    "why_it_matters": "Generic AI takes are saturated; operating lessons still stand out.",
                    "possible_angles": ["evaluation-loop lesson", "local vs cloud tradeoff"],
                    "target_audience": "builders",
                    "saturation_risk": "medium",
                    "opportunity": "Share a concrete experiment constraint.",
                }
            )
        elif "JSON" in blob.upper() and (
            "insight engine" in blob.lower()
            or "Generate the insight JSON" in blob
        ):
            broad_topic = bool(
                re.search(
                    r"Topic:\s*(AI|Artificial Intelligence|The future of AI|AI trends)\s*$",
                    blob,
                    re.I | re.M,
                )
            )
            empty_memory = "Verified experiences" in blob and re.search(
                r"Verified experiences[^\n]*:\s*\[\s*\]", blob
            )
            if broad_topic and empty_memory:
                text = json.dumps(
                    {
                        "core_insight": "AI is changing everything across industries.",
                        "why_it_matters": "The future of work depends on embracing digital transformation.",
                        "common_belief": "AI will transform every industry.",
                        "new_perspective": "AI is transforming every industry, so teams should stay ahead of the curve.",
                        "supporting_evidence": "",
                        "reader_takeaway": "Believe in yourself and unlock your potential with AI.",
                    }
                )
            else:
                text = json.dumps(
                    {
                        "core_insight": "The bottleneck in local LLM work is usually the evaluation loop, not model size.",
                        "why_it_matters": "Teams waste cycles upgrading models before measuring draft failure modes.",
                        "common_belief": "Bigger or newer models automatically produce better content.",
                        "new_perspective": "Constrained evaluation criteria and failing tests create more lift than model swaps.",
                        "supporting_evidence": "Compared local LLM workflows with cloud APIs for content drafting",
                        "reader_takeaway": "Write one failing test for generic phrasing, then compare two models against it.",
                    }
                )
        elif "JSON" in blob.upper() and ("discussion_question" in blob.lower() or "content strategist" in blob.lower() or "Produce strategy" in blob):
            text = json.dumps(
                {
                    "audience": "builders",
                    "hook": "Most advice optimizes for noise.",
                    "opinion": "Specific systems beat generic advice.",
                    "structure": "hook → observation → lesson → question",
                    "discussion_question": "What constraint are you accepting?",
                }
            )
        elif "JSON" in blob.upper() and "angles" in blob.lower():
            text = json.dumps(
                {
                    "angles": [
                        {
                            "type": "contrarian_lesson",
                            "hook": "Most advice optimizes for noise. Here's the constraint I care about.",
                            "reason": "Contrarian framing creates curiosity.",
                            "target_audience": "builders",
                        },
                        {
                            "type": "tradeoff",
                            "hook": "The useful question isn't what's trending — it's which tradeoff you accept.",
                            "reason": "Tradeoffs create discussion.",
                            "target_audience": "operators",
                        },
                        {
                            "type": "implementation_lesson",
                            "hook": "If I had to explain this in one operational lesson, it would be this.",
                            "reason": "Forces a specific takeaway.",
                            "target_audience": "engineers",
                        },
                    ]
                }
            )
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
        elif "JSON" in blob.upper() and (
            "writing-quality analyst" in blob.lower()
            or "low-quality ai writing" in blob.lower()
        ):
            text = json.dumps(
                {
                    "improvements": [
                        "Replace generic openings with a specific observation",
                        "Keep claims grounded in verified memory",
                    ]
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
                    "truth_score": 70,
                    "human_quality_score": 75,
                    "ai_pattern_risk": 25,
                    "engagement_score": 68,
                    "issues": [],
                }
            )
        else:
            text = (
                "I spent time testing this workflow, and one pattern stood out to me.\n\n"
                "I care more about specific systems than generic advice.\n\n"
                "What have you tested recently?"
            )
        return GenerateResult(text=text, model=model or "fake-model", provider=self.name)

    def _match_key(self, blob: str) -> str | None:
        for key in self.scripted:
            if key.lower() in blob.lower():
                return key
        return None
