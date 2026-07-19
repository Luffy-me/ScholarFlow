"""Apply a fixed library of mental models to evidence-grounded observations."""

from __future__ import annotations

from typing import Any

from agents.reasoning._util import claim_ref, normalize_text, top_claims
from agents.reasoning.schemas import MentalModelApplication

MENTAL_MODELS: tuple[str, ...] = (
    "First Principles",
    "Second-order Thinking",
    "Opportunity Cost",
    "Network Effects",
    "Compounding",
    "Flywheel",
    "Pareto",
    "Game Theory",
    "Inversion",
    "Systems Thinking",
    "Prisoner's Dilemma",
    "Diffusion of Innovation",
    "Jobs To Be Done",
    "Porter's Five Forces",
    "SWOT",
    "OODA Loop",
    "Bayesian Thinking",
    "Expected Value",
    "Root Cause Analysis",
    "Decision Trees",
)


_MODEL_TEMPLATES: dict[str, tuple[str, str]] = {
    "First Principles": (
        "Reduce {topic} to evidence-backed fundamentals rather than analogies.",
        "Build from verified claims upward; discard unsupported folklore.",
    ),
    "Second-order Thinking": (
        "Ask what happens after the first-order effect of {topic}.",
        "Anticipate adaptation by competitors, users, and regulators.",
    ),
    "Opportunity Cost": (
        "Choosing a path on {topic} forgoes alternative uses of scarce attention/capital.",
        "Price the next-best option explicitly before committing.",
    ),
    "Network Effects": (
        "Value of {topic} may rise (or stall) with adoption density.",
        "Map whether growth improves product quality or just vanity metrics.",
    ),
    "Compounding": (
        "Small process advantages around {topic} may compound over cycles.",
        "Prefer repeatable loops over one-off wins.",
    ),
    "Flywheel": (
        "Identify reinforcing loops that accelerate {topic}.",
        "Remove friction in the loop step that currently bottlenecks momentum.",
    ),
    "Pareto": (
        "A minority of causes likely drive most outcomes in {topic}.",
        "Concentrate on the vital few evidence-backed drivers.",
    ),
    "Game Theory": (
        "Actors around {topic} respond strategically to each other's moves.",
        "Model incentives, not intentions.",
    ),
    "Inversion": (
        "Invert: how would {topic} fail?",
        "Prevent the failure modes before optimizing upside.",
    ),
    "Systems Thinking": (
        "Treat {topic} as stocks, flows, and feedback — not isolated events.",
        "Find leverage points instead of symptomatic fixes.",
    ),
    "Prisoner's Dilemma": (
        "Short-term defection around {topic} can destroy mutual gains.",
        "Design credible commitments / repeated-game incentives.",
    ),
    "Diffusion of Innovation": (
        "Adoption of {topic} likely moves through innovators → early majority.",
        "Match messaging and product maturity to the current adopter segment.",
    ),
    "Jobs To Be Done": (
        "Users 'hire' solutions related to {topic} for a progress job.",
        "Optimize for the job, not the feature checklist.",
    ),
    "Porter's Five Forces": (
        "Industry structure around {topic} shapes sustainable advantage.",
        "Assess rivalry, substitutes, entrants, buyer/supplier power.",
    ),
    "SWOT": (
        "Catalog strengths/weaknesses/opportunities/threats for {topic} from evidence.",
        "Pair each strength with a threat it must still survive.",
    ),
    "OODA Loop": (
        "Speed of observe-orient-decide-act cycles matters for {topic}.",
        "Shorten feedback latency where evidence shows delay costs.",
    ),
    "Bayesian Thinking": (
        "Update beliefs about {topic} proportionally to new evidence strength.",
        "Avoid overreacting to weak or unverified claims.",
    ),
    "Expected Value": (
        "Compare options on {topic} by probability-weighted outcomes.",
        "Prefer positive EV even when narratives feel worse.",
    ),
    "Root Cause Analysis": (
        "Trace symptoms of {topic} to underlying constraints in evidence.",
        "Fix causes; do not celebrate proxy metrics.",
    ),
    "Decision Trees": (
        "Decompose {topic} choices into sequential uncertain branches.",
        "Identify information that most changes the decision.",
    ),
}


class MentalModelEngine:
    name = "mental_models"

    def list_models(self) -> list[str]:
        return list(MENTAL_MODELS)

    def apply(
        self,
        topic: str,
        claims: list[dict[str, Any]],
        *,
        models: list[str] | None = None,
        limit: int = 8,
    ) -> list[MentalModelApplication]:
        topic = normalize_text(topic)
        selected = models or list(MENTAL_MODELS)
        # Deterministic subset: pick models whose names sort stably, limited
        selected = sorted({m for m in selected if m in _MODEL_TEMPLATES})[: max(1, limit)]
        top = top_claims(claims, limit=3)
        refs = [claim_ref(c, i) for i, c in enumerate(top)]
        claim_text = normalize_text(str(top[0].get("claim"))) if top else ""

        apps: list[MentalModelApplication] = []
        for model in selected:
            lens, implication = _MODEL_TEMPLATES[model]
            observation = (
                f"Evidence highlights: {claim_text}"
                if claim_text
                else f"No verified claim yet for {topic}; apply {model} as a questioning lens only."
            )
            apps.append(
                MentalModelApplication(
                    model=model,
                    lens=lens.format(topic=topic),
                    observation=observation,
                    implication=implication,
                    evidence_refs=refs,
                )
            )
        return apps
