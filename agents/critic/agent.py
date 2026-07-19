"""AI Writing Critic Agent."""

from __future__ import annotations

import json
from typing import Any

from pydantic import BaseModel, Field

from agents.base import Agent, AgentInput, AgentOutput
from models.base import ChatMessage
from shared.knowledge import load_bad_posts, load_good_posts, load_user_memory
from shared.quality import clamp_score, scan_text


class CriticScores(BaseModel):
    originality: int = 0
    human_quality: int = 0
    engagement_probability: int = 0
    evidence_quality: int = 0
    ai_pattern_score: int = 0


class CriticInput(AgentInput):
    pass


class CriticOutput(AgentOutput):
    scores: CriticScores = Field(default_factory=CriticScores)
    issues: list[str] = Field(default_factory=list)


class CriticAgent(Agent[CriticInput, CriticOutput]):
    name = "critic"

    async def run(self, payload: CriticInput) -> CriticOutput:
        memory = payload.user_memory or load_user_memory()
        text = payload.text.strip()
        good = load_good_posts().get("posts", [])
        bad = load_bad_posts().get("posts", [])

        system = (
            "You are a strict LinkedIn writing critic.\n"
            "Compare the draft against good and bad examples.\n"
            "Return JSON with originality, human_quality, engagement_probability, "
            "evidence_quality, ai_pattern_score (0-100), and issues[].\n"
            "ai_pattern_score is higher when writing looks more AI-generated.\n"
            f"Good examples: {json.dumps(good[:2])}\n"
            f"Bad examples: {json.dumps(bad[:2])}"
        )
        result = await self.provider.generate(
            [
                ChatMessage(role="system", content=system),
                ChatMessage(role="user", content=text or "Empty draft"),
            ],
            temperature=0.1,
            response_format="json",
        )

        llm_scores, llm_issues = self._parse_llm(result.text)
        scan = scan_text(text, memory)
        scores, issues = self._merge_with_rules(llm_scores, llm_issues, scan, text)

        return CriticOutput(
            text=text,
            scores=scores,
            issues=issues,
            data={"quality_scan": scan.__dict__},
            meta={"provider": result.provider, "model": result.model},
        )

    def _parse_llm(self, raw: str) -> tuple[CriticScores, list[str]]:
        try:
            payload = json.loads(raw)
            scores = CriticScores(
                originality=clamp_score(payload.get("originality", 50)),
                human_quality=clamp_score(payload.get("human_quality", 50)),
                engagement_probability=clamp_score(payload.get("engagement_probability", 50)),
                evidence_quality=clamp_score(payload.get("evidence_quality", 50)),
                ai_pattern_score=clamp_score(payload.get("ai_pattern_score", 50)),
            )
            issues = [str(item) for item in payload.get("issues", [])]
            return scores, issues
        except (json.JSONDecodeError, TypeError, ValueError):
            return CriticScores(), []

    def _merge_with_rules(
        self,
        scores: CriticScores,
        issues: list[str],
        scan,
        text: str,
    ) -> tuple[CriticScores, list[str]]:
        merged_issues = list(issues)

        if scan.has_generic_ai:
            scores.ai_pattern_score = max(scores.ai_pattern_score, 85)
            scores.human_quality = min(scores.human_quality or 40, 35)
            scores.originality = min(scores.originality or 40, 30)
            merged_issues.append("Generic AI writing detected")
            for hit in scan.banned_phrases:
                merged_issues.append(f"Banned phrase: {hit.matched}")

        if scan.has_weak_hook:
            scores.engagement_probability = min(scores.engagement_probability or 40, 35)
            merged_issues.append("Weak hook identified")
            for hit in scan.weak_hooks:
                merged_issues.append(f"Weak hook pattern: {hit.matched}")

        if scan.has_fake_experience:
            scores.evidence_quality = min(scores.evidence_quality or 40, 20)
            scores.human_quality = min(scores.human_quality or 40, 25)
            merged_issues.append("Fake personal experience rejected")
            for hit in scan.fake_experiences:
                merged_issues.append(f"Ungrounded experience: {hit.matched}")

        if scan.has_strong_first_person and not scan.has_generic_ai:
            scores.human_quality = max(scores.human_quality, 70)
            scores.originality = max(scores.originality, 65)

        if not text.strip():
            merged_issues.append("Empty draft")
            scores = CriticScores(
                originality=0,
                human_quality=0,
                engagement_probability=0,
                evidence_quality=0,
                ai_pattern_score=100,
            )

        # Deduplicate while preserving order
        deduped: list[str] = []
        for item in merged_issues:
            if item not in deduped:
                deduped.append(item)
        return scores, deduped


async def critique_text(provider, *, text: str, user_memory: dict[str, Any] | None = None) -> CriticOutput:
    agent = CriticAgent(provider)
    return await agent.run(CriticInput(text=text, user_memory=user_memory or {}))
