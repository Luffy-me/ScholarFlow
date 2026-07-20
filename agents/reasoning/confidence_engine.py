"""Confidence engine — evidence quality, reasoning quality, novelty, confidence."""

from __future__ import annotations

from typing import Any

from agents.reasoning._util import mean_confidence, normalize_text, verified_ratio
from agents.reasoning.schemas import ConfidenceScore, ThoughtInsight


class ConfidenceEngine:
    name = "confidence_engine"

    def score(
        self,
        claims: list[dict[str, Any]],
        *,
        insights: list[ThoughtInsight] | None = None,
        contradictions_count: int = 0,
        hypotheses_count: int = 0,
        counterarguments_count: int = 0,
        trends: list[dict[str, Any]] | None = None,
    ) -> ConfidenceScore:
        insights = insights or []
        trends = trends or []

        evidence_quality = 0.0
        if claims:
            evidence_quality = 0.55 * mean_confidence(claims) + 0.45 * verified_ratio(claims)
            # Penalize contradictions
            evidence_quality *= max(0.4, 1.0 - 0.08 * contradictions_count)
        evidence_quality = max(0.0, min(1.0, evidence_quality))

        reasoning_quality = 0.2
        if hypotheses_count >= 2:
            reasoning_quality += 0.25  # competing hypotheses present
        if counterarguments_count >= 1:
            reasoning_quality += 0.2
        if insights:
            complete = sum(
                1
                for i in insights
                if i.why and i.why_now and i.what_changes and i.who_benefits and i.who_loses
            )
            reasoning_quality += 0.35 * (complete / max(1, len(insights)))
        reasoning_quality = max(0.0, min(1.0, reasoning_quality))

        # Novelty: reward non-generic statements + trend timing, not buzzwords
        novelty = 0.25
        if trends:
            novelty += min(0.35, float(trends[0].get("momentum") or 0) * 0.5)
        if insights:
            lengths = [len(normalize_text(i.statement)) for i in insights]
            novelty += 0.2 if (sum(lengths) / len(lengths)) >= 40 else 0.05
            if any(i.mental_models_used for i in insights):
                novelty += 0.15
        novelty = max(0.0, min(1.0, novelty))

        confidence = (
            0.45 * evidence_quality + 0.35 * reasoning_quality + 0.20 * novelty
        )
        notes: list[str] = []
        if not claims:
            notes.append("No Evidence Graph claims — confidence capped by missing facts.")
            confidence = min(confidence, 0.25)
        if contradictions_count:
            notes.append(f"{contradictions_count} contradiction(s) reduce evidence quality.")
        if hypotheses_count < 2:
            notes.append("Fewer than two hypotheses — reasoning quality reduced.")

        return ConfidenceScore(
            evidence_quality=round(evidence_quality, 4),
            reasoning_quality=round(reasoning_quality, 4),
            novelty=round(novelty, 4),
            confidence=round(max(0.0, min(1.0, confidence)), 4),
            notes=notes,
        )

    def score_insight(
        self,
        insight: ThoughtInsight,
        claims: list[dict[str, Any]],
        **kwargs: Any,
    ) -> ConfidenceScore:
        scored = self.score(claims, insights=[insight], **kwargs)
        # Require evidence refs for non-trivial confidence
        if not insight.evidence_refs:
            scored.confidence = min(scored.confidence, 0.2)
            scored.notes = list(scored.notes) + ["Insight lacks Evidence Graph references."]
        insight.confidence = scored
        return scored
