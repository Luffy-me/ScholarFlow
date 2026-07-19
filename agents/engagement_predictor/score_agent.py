"""Engagement Predictor Agent — pre-publish weakness detection."""

from __future__ import annotations

import json
from typing import Any

from pydantic import BaseModel, Field

from agents.base import Agent, AgentInput, AgentOutput
from models.base import ChatMessage
from shared.knowledge import load_user_memory
from shared.quality import clamp_score, scan_text


class EngagementScores(BaseModel):
    overall_score: int = 0
    hook_score: int = 0
    originality_score: int = 0
    specificity_score: int = 0
    discussion_score: int = 0
    ai_pattern_score: int = 0
    problems: list[str] = Field(default_factory=list)
    improvements: list[str] = Field(default_factory=list)


class EngagementPredictorInput(AgentInput):
    pass


class EngagementPredictorOutput(AgentOutput):
    scores: EngagementScores = Field(default_factory=EngagementScores)


class EngagementPredictorAgent(Agent[EngagementPredictorInput, EngagementPredictorOutput]):
    name = "engagement_predictor"

    async def run(self, payload: EngagementPredictorInput) -> EngagementPredictorOutput:
        memory = payload.user_memory or load_user_memory()
        text = payload.text.strip()
        system = (
            "Predict LinkedIn post QUALITY weaknesses before publishing.\n"
            "Do NOT claim viral success.\n"
            "Analyze hook strength, originality, specificity, story quality, "
            "discussion potential, evidence quality, emotional connection, AI-writing risk.\n"
            "Return JSON with overall_score, hook_score, originality_score, specificity_score, "
            "discussion_score, ai_pattern_score, problems[], improvements[].\n"
            "ai_pattern_score is higher when more AI-like."
        )
        result = await self.provider.generate(
            [
                ChatMessage(role="system", content=system),
                ChatMessage(role="user", content=text or "Empty draft"),
            ],
            temperature=0.1,
            response_format="json",
        )
        scores = self._parse_llm(result.text)
        scores = self._apply_rules(scores, text, memory)
        return EngagementPredictorOutput(
            text=text,
            scores=scores,
            data=scores.model_dump(),
            meta={"provider": result.provider, "model": result.model},
        )

    def _parse_llm(self, raw: str) -> EngagementScores:
        try:
            payload = json.loads(raw)
            return EngagementScores(
                overall_score=clamp_score(payload.get("overall_score", 50)),
                hook_score=clamp_score(payload.get("hook_score", 50)),
                originality_score=clamp_score(payload.get("originality_score", 50)),
                specificity_score=clamp_score(payload.get("specificity_score", 50)),
                discussion_score=clamp_score(payload.get("discussion_score", 50)),
                ai_pattern_score=clamp_score(payload.get("ai_pattern_score", 50)),
                problems=[str(p) for p in payload.get("problems", [])],
                improvements=[str(i) for i in payload.get("improvements", [])],
            )
        except (json.JSONDecodeError, TypeError, ValueError):
            return EngagementScores()

    def _apply_rules(self, scores: EngagementScores, text: str, memory: dict[str, Any]) -> EngagementScores:
        scan = scan_text(text, memory)
        problems = list(scores.problems)
        improvements = list(scores.improvements)

        if scan.has_generic_ai:
            scores.ai_pattern_score = max(scores.ai_pattern_score, 85)
            scores.originality_score = min(scores.originality_score or 40, 30)
            scores.overall_score = min(scores.overall_score or 40, 35)
            problems.append("Generic AI writing detected")
            improvements.append("Replace corporate phrases with a concrete observation")

        if scan.has_weak_hook:
            scores.hook_score = min(scores.hook_score or 40, 30)
            scores.overall_score = min(scores.overall_score or 40, 40)
            problems.append("Weak hook identified")
            improvements.append("Open with a specific moment, decision, or surprising lesson")

        if scan.has_fake_experience:
            scores.specificity_score = min(scores.specificity_score or 40, 25)
            problems.append("Ungrounded personal experience claim")
            improvements.append("Use only experiences listed in user_memory.json")

        if scan.has_strong_first_person and not scan.has_generic_ai:
            scores.hook_score = max(scores.hook_score, 65)
            scores.originality_score = max(scores.originality_score, 65)
            scores.overall_score = max(scores.overall_score, 65)

        if "?" in text:
            scores.discussion_score = max(scores.discussion_score, 60)
        else:
            improvements.append("Consider ending with a genuine discussion question")

        # Ensure structured fields always present
        scores.problems = list(dict.fromkeys(problems))
        scores.improvements = list(dict.fromkeys(improvements))
        for field_name in (
            "overall_score",
            "hook_score",
            "originality_score",
            "specificity_score",
            "discussion_score",
            "ai_pattern_score",
        ):
            setattr(scores, field_name, clamp_score(getattr(scores, field_name)))
        return scores


# Module path required by architecture docs.
async def score_post(provider, *, text: str, user_memory: dict[str, Any] | None = None) -> EngagementPredictorOutput:
    agent = EngagementPredictorAgent(provider)
    return await agent.run(EngagementPredictorInput(text=text, user_memory=user_memory or {}))
