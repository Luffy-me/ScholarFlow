"""AI Writing Critic Agent.

Evaluates:
1. Truth
2. Human authenticity
3. AI writing patterns (pattern risk — never authorship claims)
4. Engagement potential
"""

from __future__ import annotations

import json
from typing import Any

from pydantic import BaseModel, Field

from agents.base import Agent, AgentInput, AgentOutput
from agents.grounding import check_claims
from agents.writing_quality import analyze_writing_quality
from models.base import ChatMessage
from shared.knowledge import load_ai_like_posts, load_bad_posts, load_good_posts, load_human_like_posts, load_user_memory
from shared.quality import clamp_score, scan_text


class CriticScores(BaseModel):
    # Legacy fields (kept for compatibility with earlier Phase 1 tests/API)
    originality: int = 0
    human_quality: int = 0
    engagement_probability: int = 0
    evidence_quality: int = 0
    ai_pattern_score: int = 0
    # AI Writing Quality Framework scores
    truth_score: int = 0
    human_quality_score: int = 0
    ai_pattern_risk: int = 0
    engagement_score: int = 0


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
        human_like = load_human_like_posts().get("posts", [])
        ai_like = load_ai_like_posts().get("posts", [])

        system = (
            "You are a strict LinkedIn writing critic.\n"
            "Evaluate truth, human authenticity, AI-writing-pattern risk, and engagement potential.\n"
            "IMPORTANT: Never claim the draft was written by AI or by a human. "
            "Only discuss patterns associated with low-quality AI writing.\n"
            "Return JSON with originality, human_quality, engagement_probability, "
            "evidence_quality, ai_pattern_score, truth_score, human_quality_score, "
            "ai_pattern_risk, engagement_score (0-100), and issues[].\n"
            "ai_pattern_score and ai_pattern_risk are higher when more low-quality AI writing patterns appear.\n"
            f"Good examples: {json.dumps(good[:2])}\n"
            f"Bad examples: {json.dumps(bad[:2])}\n"
            f"Human-like pattern examples: {json.dumps(human_like[:1])}\n"
            f"AI-like pattern examples: {json.dumps(ai_like[:1])}"
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
        quality = payload.extra.get("writing_quality") if isinstance(payload.extra, dict) else None
        if not isinstance(quality, dict):
            quality = analyze_writing_quality(
                text,
                content_mode=payload.content_mode or "founder",
                user_memory=memory,
            ).as_report()
        grounding = check_claims(text, memory)
        scores, issues = self._merge_with_rules(
            llm_scores, llm_issues, scan, text, quality, grounding
        )

        return CriticOutput(
            text=text,
            scores=scores,
            issues=issues,
            data={
                "quality_scan": scan.__dict__,
                "writing_quality": quality,
                "truth": {
                    "safe": grounding.safe,
                    "rejected": [c.model_dump() for c in grounding.rejected_claims],
                },
            },
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
                ai_pattern_score=clamp_score(
                    payload.get("ai_pattern_score", payload.get("ai_pattern_risk", 50))
                ),
                truth_score=clamp_score(payload.get("truth_score", payload.get("evidence_quality", 50))),
                human_quality_score=clamp_score(
                    payload.get("human_quality_score", payload.get("human_quality", 50))
                ),
                ai_pattern_risk=clamp_score(
                    payload.get("ai_pattern_risk", payload.get("ai_pattern_score", 50))
                ),
                engagement_score=clamp_score(
                    payload.get("engagement_score", payload.get("engagement_probability", 50))
                ),
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
        quality: dict[str, Any],
        grounding,
    ) -> tuple[CriticScores, list[str]]:
        merged_issues = list(issues)

        # Framework scores take priority when present.
        if quality:
            scores.ai_pattern_risk = max(
                scores.ai_pattern_risk,
                clamp_score(quality.get("ai_pattern_risk", 0)),
            )
            scores.human_quality_score = clamp_score(
                quality.get("human_quality_score", scores.human_quality_score or scores.human_quality)
            )
            scores.originality = max(
                scores.originality,
                clamp_score(quality.get("originality_score", scores.originality)),
            )
            for pattern in quality.get("detected_patterns") or []:
                category = pattern.get("category", "pattern")
                example = pattern.get("example", "")
                merged_issues.append(
                    f"AI writing pattern ({category}): {example}".strip(": ")
                )

        if scan.has_generic_ai:
            scores.ai_pattern_score = max(scores.ai_pattern_score, 85)
            scores.ai_pattern_risk = max(scores.ai_pattern_risk, 85)
            scores.human_quality = min(scores.human_quality or 40, 35)
            scores.human_quality_score = min(scores.human_quality_score or 40, 35)
            scores.originality = min(scores.originality or 40, 30)
            merged_issues.append("Generic AI writing detected")
            for hit in scan.banned_phrases:
                merged_issues.append(f"Banned phrase: {hit.matched}")

        if scan.has_weak_hook:
            scores.engagement_probability = min(scores.engagement_probability or 40, 35)
            scores.engagement_score = min(scores.engagement_score or 40, 35)
            merged_issues.append("Weak hook identified")
            for hit in scan.weak_hooks:
                merged_issues.append(f"Weak hook pattern: {hit.matched}")

        if scan.has_fake_experience or not grounding.safe:
            scores.evidence_quality = min(scores.evidence_quality or 40, 20)
            scores.truth_score = min(scores.truth_score or 40, 20)
            scores.human_quality = min(scores.human_quality or 40, 25)
            scores.human_quality_score = min(scores.human_quality_score or 40, 25)
            merged_issues.append("Fake personal experience rejected")
            for hit in scan.fake_experiences:
                merged_issues.append(f"Ungrounded experience: {hit.matched}")
            for claim in grounding.rejected_claims:
                merged_issues.append(f"Truth Layer rejected {claim.claim_type}: {claim.text[:100]}")
        else:
            scores.truth_score = max(scores.truth_score, scores.evidence_quality, 70)
            scores.evidence_quality = max(scores.evidence_quality, 60)

        if scan.has_strong_first_person and not scan.has_generic_ai:
            scores.human_quality = max(scores.human_quality, 70)
            scores.human_quality_score = max(scores.human_quality_score, 70)
            scores.originality = max(scores.originality, 65)

        # Synchronize legacy score names with framework fields.
        if quality:
            scores.human_quality = scores.human_quality_score or scores.human_quality
        scores.ai_pattern_score = max(scores.ai_pattern_score, scores.ai_pattern_risk)
        scores.ai_pattern_risk = max(scores.ai_pattern_risk, scores.ai_pattern_score)
        scores.engagement_score = max(scores.engagement_score, scores.engagement_probability)
        scores.engagement_probability = max(scores.engagement_probability, scores.engagement_score)
        if not scores.truth_score:
            scores.truth_score = scores.evidence_quality
        if not scores.human_quality_score:
            scores.human_quality_score = scores.human_quality

        if not text.strip():
            merged_issues.append("Empty draft")
            scores = CriticScores(
                originality=0,
                human_quality=0,
                engagement_probability=0,
                evidence_quality=0,
                ai_pattern_score=100,
                truth_score=0,
                human_quality_score=0,
                ai_pattern_risk=100,
                engagement_score=0,
            )

        deduped: list[str] = []
        for item in merged_issues:
            if item not in deduped:
                deduped.append(item)
        return scores, deduped


async def critique_text(provider, *, text: str, user_memory: dict[str, Any] | None = None) -> CriticOutput:
    agent = CriticAgent(provider)
    return await agent.run(CriticInput(text=text, user_memory=user_memory or {}))
