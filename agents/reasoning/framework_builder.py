"""Automatically create reusable frameworks from reasoning context."""

from __future__ import annotations

from typing import Any

from agents.reasoning._util import claim_ref, normalize_text, top_claims
from agents.reasoning.schemas import Framework

FRAMEWORK_KINDS: tuple[str, ...] = (
    "3-Step Framework",
    "5-Step Framework",
    "Decision Matrix",
    "Flywheel",
    "Pyramid",
    "Checklist",
    "Roadmap",
)


class FrameworkBuilder:
    name = "framework_builder"

    def build(
        self,
        topic: str,
        claims: list[dict[str, Any]],
        *,
        hypotheses: list[Any] | None = None,
        tradeoffs: list[Any] | None = None,
    ) -> list[Framework]:
        topic = normalize_text(topic)
        top = top_claims(claims, limit=5)
        refs = [claim_ref(c, i) for i, c in enumerate(top)]
        claim_steps = [
            f"Account for: {normalize_text(str(c.get('claim')))}"
            for c in top[:3]
        ]
        while len(claim_steps) < 3:
            claim_steps.append(f"Collect missing evidence on {topic} (no claim available).")

        frameworks: list[Framework] = [
            Framework(
                name=f"{topic} 3-Step Operating Loop",
                kind="3-Step Framework",
                steps=[
                    f"1. Diagnose with Evidence Graph claims for {topic}",
                    f"2. {claim_steps[0]}",
                    f"3. Decide and instrument a feedback metric",
                ],
                description="Compact operating loop grounded in evidence.",
                evidence_refs=refs,
            ),
            Framework(
                name=f"{topic} 5-Step Analysis",
                kind="5-Step Framework",
                steps=[
                    "1. State the problem without slogans",
                    "2. List competing hypotheses",
                    f"3. {claim_steps[0]}",
                    f"4. {claim_steps[1] if len(claim_steps) > 1 else claim_steps[0]}",
                    "5. Choose action; schedule disconfirming checks",
                ],
                description="Research-scientist style analysis scaffold.",
                evidence_refs=refs,
            ),
            Framework(
                name=f"{topic} Decision Matrix",
                kind="Decision Matrix",
                steps=[
                    "Rows: options under consideration",
                    "Columns: evidence strength, upside, downside, irreversibility",
                    "Score only with Evidence Graph support — blank cells mean unknown",
                    "Select the option with best constrained score, not best narrative",
                ],
                description="McKinsey-style option comparison.",
                evidence_refs=refs,
            ),
            Framework(
                name=f"{topic} Flywheel",
                kind="Flywheel",
                steps=[
                    f"Signal → Insight about {topic}",
                    "Insight → Decision",
                    "Decision → Action",
                    "Action → Measured outcome",
                    "Outcome → Stronger signal",
                ],
                description="Compounding learning flywheel.",
                evidence_refs=refs,
            ),
            Framework(
                name=f"{topic} Pyramid",
                kind="Pyramid",
                steps=[
                    f"Governing thought: what must be true about {topic}",
                    "Supporting pillars = top evidence claims",
                    "Base facts = source refs only (no invented data)",
                ],
                description="Minto pyramid for executive communication of thoughts.",
                evidence_refs=refs,
            ),
            Framework(
                name=f"{topic} Evidence Checklist",
                kind="Checklist",
                steps=[
                    "Every assertion has an Evidence Graph ref",
                    "Competing hypothesis recorded",
                    "Counterargument reviewed",
                    "Missing evidence listed",
                    "Confidence scored (evidence + reasoning + novelty)",
                ],
                description="Quality gate before shipping a conclusion.",
                evidence_refs=refs,
            ),
            Framework(
                name=f"{topic} 90-Day Roadmap",
                kind="Roadmap",
                steps=[
                    "Days 0–30: validate or kill the primary hypothesis",
                    "Days 31–60: instrument the highest-leverage constraint",
                    "Days 61–90: scale only what evidence still supports",
                ],
                description="Founder/product roadmap with kill-criteria.",
                evidence_refs=refs,
            ),
        ]

        if hypotheses:
            frameworks.append(
                Framework(
                    name=f"{topic} Hypothesis Ladder",
                    kind="Checklist",
                    steps=[
                        f"Test: {getattr(h, 'statement', h)}"
                        for h in hypotheses[:4]
                    ],
                    description="Ordered tests for competing hypotheses.",
                    evidence_refs=refs,
                )
            )
        if tradeoffs:
            frameworks.append(
                Framework(
                    name=f"{topic} Tradeoff Board",
                    kind="Decision Matrix",
                    steps=[
                        f"{getattr(t, 'dimension_a', 'A')} vs {getattr(t, 'dimension_b', 'B')}"
                        for t in tradeoffs[:4]
                    ],
                    description="Explicit trade-off board from analysis.",
                    evidence_refs=refs,
                )
            )
        return frameworks
