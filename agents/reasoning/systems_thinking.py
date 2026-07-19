"""Systems thinking — stocks, flows, feedback, leverage points."""

from __future__ import annotations

from typing import Any

from agents.reasoning._util import claim_ref, knowledge_summary, normalize_text, top_claims
from agents.reasoning.schemas import SystemMap


class SystemsThinkingEngine:
    name = "systems_thinking"

    def map_system(
        self,
        topic: str,
        claims: list[dict[str, Any]],
        *,
        knowledge_graph: Any = None,
    ) -> SystemMap:
        topic = normalize_text(topic)
        top = top_claims(claims, limit=5)
        refs = [claim_ref(c, i) for i, c in enumerate(top)]
        kg = knowledge_summary(knowledge_graph)
        labels = kg.get("labels") or []

        stocks = [
            f"Stock: accumulated knowledge about {topic}",
            f"Stock: unresolved open questions on {topic}",
        ]
        if labels:
            stocks.append(f"Stock: conceptual nodes ({len(labels)}) in Knowledge Graph")

        flows = [
            "Flow: new evidence claims enter the Evidence Graph",
            "Flow: decisions convert insight into action",
            "Flow: outcomes update confidence (Bayesian refresh)",
        ]
        if top:
            flows.append(f"Flow driven by claim: {normalize_text(str(top[0].get('claim')))}")

        loops = [
            "Reinforcing: better evidence → better decisions → better outcomes → more evidence",
            "Balancing: overconfidence → weak probes → contradictory results → belief reset",
        ]
        if kg.get("contradict_edges"):
            loops.append("Balancing: Knowledge Graph contradictions slow premature closure")

        leverage = [
            "Improve evidence quality (verification) before scaling action",
            "Shorten feedback latency between action and measured outcome",
        ]
        if top:
            leverage.append(
                f"Intervene on the constraint implied by: {normalize_text(str(top[0].get('claim')))}"
            )

        return SystemMap(
            stocks=stocks,
            flows=flows,
            feedback_loops=loops,
            leverage_points=leverage,
            evidence_refs=refs,
        )
