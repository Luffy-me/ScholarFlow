"""Analogy engine — structured mappings with explicit caution (no false facts)."""

from __future__ import annotations

from typing import Any

from agents.reasoning._util import claim_ref, normalize_text, top_claims
from agents.reasoning.schemas import Analogy

_DOMAIN_PAIRS: tuple[tuple[str, str], ...] = (
    ("research science", "product strategy"),
    ("economics", "startup growth"),
    ("systems engineering", "organizational design"),
    ("game theory", "competitive markets"),
    ("epidemiology", "idea diffusion"),
)


class AnalogyEngine:
    name = "analogy_engine"

    def generate(
        self,
        topic: str,
        claims: list[dict[str, Any]],
        *,
        limit: int = 3,
    ) -> list[Analogy]:
        topic = normalize_text(topic)
        top = top_claims(claims, limit=3)
        refs = [claim_ref(c, i) for i, c in enumerate(top)]
        claim_bit = normalize_text(str(top[0].get("claim"))) if top else ""

        analogies: list[Analogy] = []
        for source, target in _DOMAIN_PAIRS[:limit]:
            mapping = (
                f"Map {topic} from {source} → {target}"
                + (f" using evidence: {claim_bit}" if claim_bit else " (evidence sparse — analogy is heuristic only)")
            )
            analogies.append(
                Analogy(
                    source_domain=source,
                    target_domain=target,
                    mapping=mapping,
                    caution=(
                        "Analogies are not evidence. Do not treat the mapping as a factual claim "
                        "unless the Evidence Graph supports the transferred mechanism."
                    ),
                    evidence_refs=refs,
                )
            )
        return analogies
