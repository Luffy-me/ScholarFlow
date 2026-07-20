"""Scenario simulator — best / expected / worst cases."""

from __future__ import annotations

from typing import Any

from agents.reasoning._util import claim_ref, normalize_text, top_claims
from agents.reasoning.schemas import Scenario


class ScenarioSimulator:
    name = "scenario_simulator"

    def simulate(
        self,
        topic: str,
        claims: list[dict[str, Any]],
        *,
        trends: list[dict[str, Any]] | None = None,
        decision: Any = None,
    ) -> list[Scenario]:
        topic = normalize_text(topic)
        top = top_claims(claims, limit=4)
        refs = [claim_ref(c, i) for i, c in enumerate(top)]
        trends = trends or []
        trend_text = normalize_text(str(trends[0].get("trend"))) if trends else ""
        claim_text = normalize_text(str(top[0].get("claim"))) if top else "limited evidence"
        recommended = ""
        if decision is not None:
            if hasattr(decision, "recommended"):
                recommended = normalize_text(str(decision.recommended or ""))
            elif isinstance(decision, dict):
                recommended = normalize_text(str(decision.get("recommended") or ""))

        return [
            Scenario(
                label="best",
                narrative=(
                    f"Best case for {topic}: evidence claim '{claim_text}' generalizes, "
                    f"feedback loops compound, and decisions remain falsifiable."
                ),
                triggers=[
                    "Verified claims accumulate",
                    "Contradictions resolve toward the primary hypothesis",
                ]
                + ([f"Trend strengthens: {trend_text}"] if trend_text else []),
                outcomes=[
                    "Higher confidence score",
                    "Clear invest/scale decision becomes justified",
                ],
                evidence_refs=refs,
            ),
            Scenario(
                label="expected",
                narrative=(
                    f"Expected case for {topic}: mixed evidence persists; "
                    f"{recommended or 'a cheap experiment'} updates beliefs gradually."
                ),
                triggers=[
                    "Some claims verify, others remain weak",
                    "Trade-offs stay binding",
                ],
                outcomes=[
                    "Iterate with probes",
                    "Avoid irreversible commitments",
                ],
                evidence_refs=refs,
            ),
            Scenario(
                label="worst",
                narrative=(
                    f"Worst case for {topic}: the primary claim fails, selection bias dominated, "
                    f"and actions based on incomplete Evidence Graph create costly lock-in."
                ),
                triggers=[
                    "Contradicting sources dominate",
                    "Unverified claims were treated as facts",
                ],
                outcomes=[
                    "Forced strategy reset",
                    "Trust / capital burn",
                ],
                evidence_refs=refs,
            ),
        ]
