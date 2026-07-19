"""Trade-off analysis — explicit A vs B with costs grounded in evidence context."""

from __future__ import annotations

from typing import Any

from agents.reasoning._util import claim_ref, normalize_text, top_claims
from agents.reasoning.schemas import Tradeoff


class TradeoffAnalyzer:
    name = "tradeoff_analysis"

    def analyze(
        self,
        topic: str,
        claims: list[dict[str, Any]],
        *,
        opportunity: dict[str, Any] | None = None,
    ) -> list[Tradeoff]:
        topic = normalize_text(topic)
        top = top_claims(claims, limit=4)
        refs = [claim_ref(c, i) for i, c in enumerate(top)]
        opportunity = opportunity or {}
        audience = normalize_text(str(opportunity.get("target_audience") or "operators"))

        tradeoffs = [
            Tradeoff(
                dimension_a="Speed",
                dimension_b="Evidence rigor",
                choose_a_when=f"Timing window for {topic} is closing and downside is reversible",
                choose_b_when="Claims are unverified or contradictions are present",
                cost_of_a="Higher false-positive risk",
                cost_of_b="Opportunity cost / delayed learning",
                evidence_refs=refs,
            ),
            Tradeoff(
                dimension_a="Breadth of bets",
                dimension_b="Depth on one thesis",
                choose_a_when="Hypotheses still compete with similar confidence",
                choose_b_when="One claim is verified and high-confidence",
                cost_of_a="Diluted learning signal",
                cost_of_b="Concentration risk if thesis is wrong",
                evidence_refs=refs,
            ),
            Tradeoff(
                dimension_a=f"Serve {audience}",
                dimension_b="Serve adjacent segments",
                choose_a_when="Opportunity engine points to a clear audience",
                choose_b_when="Evidence shows segmented realities / contradictions",
                cost_of_a="Missed expansion",
                cost_of_b="Weaker product-market focus",
                evidence_refs=refs,
            ),
            Tradeoff(
                dimension_a="Automation / scale",
                dimension_b="Human judgment loops",
                choose_a_when="Process is stable and metrics are trustworthy",
                choose_b_when=f"Root constraints around {topic} are still poorly measured",
                cost_of_a="Scaling a broken loop",
                cost_of_b="Throughput limits",
                evidence_refs=refs,
            ),
        ]
        return tradeoffs
