"""First-principles decomposition grounded only in Evidence Graph claims."""

from __future__ import annotations

from typing import Any

from agents.reasoning._util import claim_ref, normalize_text, top_claims
from agents.reasoning.schemas import FirstPrinciplesBreakdown


class FirstPrinciplesEngine:
    name = "first_principles"

    def analyze(self, topic: str, claims: list[dict[str, Any]]) -> FirstPrinciplesBreakdown:
        topic = normalize_text(topic)
        top = top_claims(claims, limit=5)
        if not top:
            return FirstPrinciplesBreakdown(
                problem=topic,
                fundamentals=[
                    "No Evidence Graph claims available — fundamentals cannot be asserted as facts.",
                ],
                derived_implications=[
                    "Gather verified claims before deriving operational implications.",
                ],
                evidence_refs=[],
            )

        fundamentals = [
            f"Observable claim: {normalize_text(str(c.get('claim')))}"
            for c in top
        ]
        derived = [
            f"If '{normalize_text(str(c.get('claim')))}' holds, designs for {topic} must account for it."
            for c in top[:3]
        ]
        # Strip slogans: only implications that cite claims
        return FirstPrinciplesBreakdown(
            problem=topic,
            fundamentals=fundamentals,
            derived_implications=derived,
            evidence_refs=[claim_ref(c, i) for i, c in enumerate(top)],
        )
