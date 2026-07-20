"""Decision engine — expected-value style choice among evidence-grounded options."""

from __future__ import annotations

from typing import Any

from agents.reasoning._util import claim_ref, normalize_text, top_claims
from agents.reasoning.schemas import DecisionOption, DecisionRecommendation


class DecisionEngine:
    name = "decision_engine"

    def decide(
        self,
        topic: str,
        claims: list[dict[str, Any]],
        *,
        opportunity: dict[str, Any] | None = None,
        tradeoffs: list[Any] | None = None,
    ) -> DecisionRecommendation:
        topic = normalize_text(topic)
        top = top_claims(claims, limit=4)
        refs = [claim_ref(c, i) for i, c in enumerate(top)]
        opportunity = opportunity or {}

        options = [
            DecisionOption(
                option=f"Invest / double-down on {topic}",
                expected_value_note="Positive if evidence confidence and opportunity score are both elevated.",
                risks=["Overfit to incomplete Evidence Graph", "Opportunity cost vs alternatives"],
                upside=["Capture timing advantage", "Compound learning flywheel"],
                evidence_refs=refs,
            ),
            DecisionOption(
                option=f"Probe with a cheap experiment on {topic}",
                expected_value_note="Default under uncertainty — buy information before irreversible spend.",
                risks=["Too-small experiment fails to falsify"],
                upside=["Updates Bayesian belief with new evidence", "Limits downside"],
                evidence_refs=refs,
            ),
            DecisionOption(
                option=f"Wait / monitor {topic}",
                expected_value_note="Rational when evidence is weak or contradictions dominate.",
                risks=["Miss irreversible timing window"],
                upside=["Avoid false positives", "Preserve optionality"],
                evidence_refs=refs,
            ),
        ]

        avg_conf = (
            sum(float(c.get("confidence") or 0) for c in top) / len(top) if top else 0.0
        )
        opp_score = float(opportunity.get("score") or 0.0)
        verified = sum(1 for c in top if c.get("verified"))

        if not top or avg_conf < 0.4:
            recommended = options[2].option
            rule = "Insufficient or weak Evidence Graph → wait/monitor."
        elif avg_conf >= 0.7 and verified >= 1 and opp_score >= 60:
            recommended = options[0].option
            rule = "Strong verified evidence + opportunity score ≥ 60 → invest."
        else:
            recommended = options[1].option
            rule = "Mixed signal → cheap experiment to falsify primary hypothesis."

        if tradeoffs:
            rule += " Explicit trade-offs recorded before commitment."

        return DecisionRecommendation(
            question=f"What should we do about {topic}?",
            options=options,
            recommended=recommended,
            decision_rule=rule,
            evidence_refs=refs,
        )
