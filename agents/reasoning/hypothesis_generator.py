"""Generate multiple competing hypotheses — never assume one explanation."""

from __future__ import annotations

from typing import Any

from agents.reasoning._util import claim_ref, normalize_text, stable_id, top_claims
from agents.reasoning.schemas import Hypothesis


class HypothesisGenerator:
    name = "hypothesis_generator"

    def generate(
        self,
        topic: str,
        claims: list[dict[str, Any]],
        *,
        trends: list[dict[str, Any]] | None = None,
        contradictions: list[Any] | None = None,
    ) -> list[Hypothesis]:
        topic = normalize_text(topic)
        top = top_claims(claims, limit=6)
        trends = trends or []
        hypotheses: list[Hypothesis] = []

        if not top:
            # No evidence → explicit uncertainty hypotheses only (no invented facts)
            h_ids = [
                stable_id("hyp", topic, "insufficient-evidence"),
                stable_id("hyp", topic, "measurement-gap"),
            ]
            return [
                Hypothesis(
                    id=h_ids[0],
                    statement=f"Insufficient evidence to explain {topic}; any single narrative is premature.",
                    rationale="Evidence graph contains no usable claims.",
                    competing_with=[h_ids[1]],
                    evidence_refs=[],
                    confidence=0.1,
                ),
                Hypothesis(
                    id=h_ids[1],
                    statement=f"The apparent pattern around {topic} may reflect a measurement gap rather than a real shift.",
                    rationale="Without claims, observation error remains a competing explanation.",
                    competing_with=[h_ids[0]],
                    evidence_refs=[],
                    confidence=0.1,
                ),
            ]

        # H1: primary evidence-driven explanation
        primary = top[0]
        h1_id = stable_id("hyp", topic, "primary", str(primary.get("claim")))
        hypotheses.append(
            Hypothesis(
                id=h1_id,
                statement=(
                    f"The dominant driver for {topic} is: {normalize_text(str(primary.get('claim')))}."
                ),
                rationale="Highest-ranked evidence claim in the Evidence Graph.",
                evidence_refs=[claim_ref(primary, 0)],
                confidence=float(primary.get("confidence") or 0.5),
            )
        )

        # H2: alternative from second claim or contradiction
        if len(top) > 1:
            alt = top[1]
            h2_id = stable_id("hyp", topic, "alt", str(alt.get("claim")))
            hypotheses.append(
                Hypothesis(
                    id=h2_id,
                    statement=(
                        f"An alternative explanation for {topic} is: {normalize_text(str(alt.get('claim')))}."
                    ),
                    rationale="Competing claim from Evidence Graph — do not collapse to one story.",
                    competing_with=[h1_id],
                    evidence_refs=[claim_ref(alt, 1)],
                    confidence=float(alt.get("confidence") or 0.45),
                )
            )
            hypotheses[0].competing_with = [h2_id]
        else:
            h2_id = stable_id("hyp", topic, "selection-bias")
            hypotheses.append(
                Hypothesis(
                    id=h2_id,
                    statement=(
                        f"Observed signals about {topic} may be selection bias in available sources "
                        f"rather than a structural change."
                    ),
                    rationale="Single-claim regimes require a bias/noise competing hypothesis.",
                    competing_with=[h1_id],
                    evidence_refs=[claim_ref(primary, 0)],
                    confidence=max(0.15, 1.0 - float(primary.get("confidence") or 0.5)),
                )
            )
            hypotheses[0].competing_with = [h2_id]

        # H3: trend-timed hypothesis (only if trend text exists)
        if trends:
            trend = trends[0]
            h3_id = stable_id("hyp", topic, "timing", str(trend.get("trend")))
            hypotheses.append(
                Hypothesis(
                    id=h3_id,
                    statement=(
                        f"Timing matters: {normalize_text(str(trend.get('trend')))} "
                        f"makes {topic} newly actionable now."
                    ),
                    rationale="Trend data supplies a why-now hypothesis distinct from root-cause claims.",
                    competing_with=[h.id for h in hypotheses[:2]],
                    evidence_refs=list(trend.get("supporting_sources") or [])[:5],
                    confidence=float(trend.get("confidence") or 0.4),
                )
            )

        # H4: contradiction-aware hypothesis
        if contradictions:
            c0 = contradictions[0]
            tension = getattr(c0, "tension", None) or (
                c0.get("tension") if isinstance(c0, dict) else "conflicting claims"
            )
            h4_id = stable_id("hyp", topic, "contradiction", str(tension))
            hypotheses.append(
                Hypothesis(
                    id=h4_id,
                    statement=(
                        f"Conflicting evidence implies {topic} has segmented realities: {normalize_text(str(tension))}."
                    ),
                    rationale="Contradictions in Evidence Graph / Knowledge Graph must produce a split hypothesis.",
                    competing_with=[h.id for h in hypotheses[:2]],
                    evidence_refs=list(getattr(c0, "source_refs", None) or (c0.get("source_refs") if isinstance(c0, dict) else []) or [])[:5],
                    confidence=0.45,
                )
            )

        # Wire mutual competition for first two
        if len(hypotheses) >= 2:
            ids = [h.id for h in hypotheses]
            for h in hypotheses:
                h.competing_with = [i for i in ids if i != h.id][:3]
        return hypotheses
