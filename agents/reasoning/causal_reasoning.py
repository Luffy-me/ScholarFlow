"""Causal reasoning — only propose links anchored to Evidence Graph claims."""

from __future__ import annotations

from typing import Any

from agents.reasoning._util import claim_ref, normalize_text, top_claims
from agents.reasoning.schemas import CausalLink


class CausalReasoningEngine:
    name = "causal_reasoning"

    def infer(
        self,
        topic: str,
        claims: list[dict[str, Any]],
        *,
        trends: list[dict[str, Any]] | None = None,
    ) -> list[CausalLink]:
        topic = normalize_text(topic)
        top = top_claims(claims, limit=5)
        trends = trends or []
        links: list[CausalLink] = []

        if not top:
            return [
                CausalLink(
                    cause="unknown (no Evidence Graph claims)",
                    effect=topic,
                    mechanism="Cannot assert causation without evidence.",
                    evidence_refs=[],
                    confidence=0.0,
                )
            ]

        for i, claim in enumerate(top):
            text = normalize_text(str(claim.get("claim")))
            links.append(
                CausalLink(
                    cause=text,
                    effect=f"Observed dynamics in {topic}",
                    mechanism=(
                        "Claim treated as a candidate cause; requires disconfirming tests "
                        "before policy reliance."
                    ),
                    evidence_refs=[claim_ref(claim, i)],
                    confidence=float(claim.get("confidence") or 0.0) * 0.9,
                )
            )

        if trends:
            trend = trends[0]
            links.append(
                CausalLink(
                    cause=normalize_text(str(trend.get("trend"))),
                    effect=f"Timing pressure on {topic}",
                    mechanism="Trend momentum is a timing factor, not proof of root cause.",
                    evidence_refs=list(trend.get("supporting_sources") or [])[:5],
                    confidence=float(trend.get("confidence") or 0.0) * 0.7,
                )
            )
        return links
