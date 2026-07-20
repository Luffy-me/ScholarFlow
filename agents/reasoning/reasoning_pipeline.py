"""Reasoning Pipeline — deterministic thought generation grounded in Evidence Graph."""

from __future__ import annotations

from typing import Any

from agents.reasoning.analogy_engine import AnalogyEngine
from agents.reasoning.causal_reasoning import CausalReasoningEngine
from agents.reasoning.confidence_engine import ConfidenceEngine
from agents.reasoning.counter_argument import CounterArgumentEngine
from agents.reasoning.decision_engine import DecisionEngine
from agents.reasoning.first_principles import FirstPrinciplesEngine
from agents.reasoning.framework_builder import FrameworkBuilder
from agents.reasoning.hypothesis_generator import HypothesisGenerator
from agents.reasoning.mental_models import MentalModelEngine
from agents.reasoning.reflection import ReflectionEngine
from agents.reasoning.scenario_simulator import ScenarioSimulator
from agents.reasoning.schemas import (
    Assumption,
    Contradiction,
    ReasoningInput,
    ReasoningOutput,
    ReasoningPacket,
    ThoughtInsight,
)
from agents.reasoning.systems_thinking import SystemsThinkingEngine
from agents.reasoning.tradeoff_analysis import TradeoffAnalyzer
from agents.reasoning._util import (
    claim_ref,
    extract_claims,
    extract_opportunity,
    extract_research,
    extract_trends,
    knowledge_summary,
    normalize_text,
    refs_for_claims,
    top_claims,
    topic_or_default,
)


class ReasoningPipeline:
    """
    Research → assumptions → contradictions → hypotheses → first principles →
    mental models → frameworks → trade-offs → counterarguments → insights → confidence.
    """

    name = "reasoning_pipeline"

    def __init__(self) -> None:
        self.hypotheses = HypothesisGenerator()
        self.first_principles = FirstPrinciplesEngine()
        self.mental_models = MentalModelEngine()
        self.frameworks = FrameworkBuilder()
        self.tradeoffs = TradeoffAnalyzer()
        self.counters = CounterArgumentEngine()
        self.decisions = DecisionEngine()
        self.analogies = AnalogyEngine()
        self.causal = CausalReasoningEngine()
        self.systems = SystemsThinkingEngine()
        self.scenarios = ScenarioSimulator()
        self.confidence = ConfidenceEngine()
        self.reflection = ReflectionEngine()

    def extract_assumptions(
        self, topic: str, claims: list[dict[str, Any]], research: dict[str, Any]
    ) -> list[Assumption]:
        assumptions: list[Assumption] = []
        for i, claim in enumerate(top_claims(claims, limit=5)):
            assumptions.append(
                Assumption(
                    statement=f"Assume true: {normalize_text(str(claim.get('claim')))}",
                    source_refs=[claim_ref(claim, i)],
                    risk_if_wrong="Downstream hypotheses and decisions become invalid.",
                )
            )
        for q in list(research.get("open_questions") or [])[:3]:
            assumptions.append(
                Assumption(
                    statement=f"Unresolved assumption / open question: {normalize_text(str(q))}",
                    source_refs=refs_for_claims(claims)[:3],
                    risk_if_wrong="Hidden unknown may dominate outcomes.",
                )
            )
        if not assumptions:
            assumptions.append(
                Assumption(
                    statement=f"No Evidence Graph claims for {topic}; all further reasoning is provisional.",
                    source_refs=[],
                    risk_if_wrong="High — acting would rely on hallucination risk.",
                )
            )
        return assumptions

    def identify_contradictions(
        self,
        claims: list[dict[str, Any]],
        knowledge_graph: Any,
    ) -> list[Contradiction]:
        contradictions: list[Contradiction] = []
        # From evidence contradicting_sources
        for i, claim in enumerate(claims):
            contras = list(claim.get("contradicting_sources") or [])
            if contras:
                contradictions.append(
                    Contradiction(
                        claim_a=normalize_text(str(claim.get("claim"))),
                        claim_b=f"Contradicted by sources: {', '.join(str(s) for s in contras[:3])}",
                        source_refs=[claim_ref(claim, i)] + [str(s) for s in contras[:3]],
                        tension="Evidence Graph marks direct contradiction.",
                    )
                )
        # Pairwise tension when two high-confidence claims share few tokens but same topic basket
        top = top_claims(claims, limit=4)
        if len(top) >= 2:
            a, b = top[0], top[1]
            ta = set(normalize_text(str(a.get("claim"))).lower().split())
            tb = set(normalize_text(str(b.get("claim"))).lower().split())
            if len(ta & tb) <= 2:
                contradictions.append(
                    Contradiction(
                        claim_a=normalize_text(str(a.get("claim"))),
                        claim_b=normalize_text(str(b.get("claim"))),
                        source_refs=[claim_ref(a, 0), claim_ref(b, 1)],
                        tension="Top claims emphasize different drivers — possible segmented explanation.",
                    )
                )
        kg = knowledge_summary(knowledge_graph)
        for edge in kg.get("contradict_edges") or []:
            contradictions.append(
                Contradiction(
                    claim_a=str(edge.get("source") or ""),
                    claim_b=str(edge.get("target") or ""),
                    source_refs=[str(edge.get("id") or "kg:contradicts")],
                    tension="Knowledge Graph edge relation=contradicts.",
                )
            )
        return contradictions

    def synthesize_insights(
        self,
        topic: str,
        *,
        claims: list[dict[str, Any]],
        hypotheses: list[Any],
        mental_models: list[Any],
        trends: list[dict[str, Any]],
        opportunity: dict[str, Any],
        tradeoffs: list[Any],
        counters: list[Any],
    ) -> list[ThoughtInsight]:
        top = top_claims(claims, limit=3)
        refs = refs_for_claims(top)
        models_used = [m.model for m in mental_models[:5]]
        hyp_ids = [h.id for h in hypotheses[:3]]
        trend_text = normalize_text(str(trends[0].get("trend"))) if trends else ""
        opp_angle = normalize_text(str(opportunity.get("recommended_angle") or ""))
        audience = normalize_text(str(opportunity.get("target_audience") or "builders"))
        primary = normalize_text(str(top[0].get("claim"))) if top else ""
        counter_missing = []
        if counters:
            counter_missing = list(counters[0].missing_evidence)[:3]

        insights: list[ThoughtInsight] = []

        statement = (
            f"For {topic}, the working thesis is evidence-linked: {primary}"
            if primary
            else f"For {topic}, evidence is insufficient for a firm thesis."
        )
        insights.append(
            ThoughtInsight(
                statement=statement,
                why=(
                    f"Because the Evidence Graph ranks this claim highest among available sources."
                    if primary
                    else "Because the Evidence Graph has no usable claims."
                ),
                why_now=(
                    f"Trend signal: {trend_text}."
                    if trend_text
                    else "No strong trend timing signal; urgency is not evidence-backed."
                ),
                what_changes=(
                    f"Operating choices should shift toward constraints implied by: {primary}"
                    if primary
                    else "No evidenced change mandate yet."
                ),
                who_benefits=f"{audience} who act on verified constraints first",
                who_loses="Actors optimizing vanity metrics that ignore the evidenced constraint",
                what_happens_next=(
                    "Run a falsifying probe on the primary hypothesis before irreversible spend."
                ),
                risks=[
                    "Treating unverified claims as facts",
                    "Ignoring competing hypotheses",
                ],
                what_is_missing=counter_missing
                or [
                    "Stronger causal measurements",
                    "Disconfirming segment data",
                ],
                evidence_refs=refs,
                mental_models_used=models_used,
                hypothesis_ids=hyp_ids,
            )
        )

        if len(hypotheses) >= 2:
            insights.append(
                ThoughtInsight(
                    statement=(
                        f"Do not collapse {topic} to one explanation — "
                        f"at least two competing hypotheses remain live."
                    ),
                    why="Hypothesis Generator enforces competing explanations from Evidence Graph inputs.",
                    why_now="Premature closure is especially costly while trends/opportunities are still forming.",
                    what_changes="Decision process must keep an explicit alternative hypothesis.",
                    who_benefits="Teams that preserve optionality and learning speed",
                    who_loses="Narratives that demand certainty without evidence",
                    what_happens_next="Design the cheapest test that distinguishes H1 vs H2.",
                    risks=["False confidence from a single story"],
                    what_is_missing=["Head-to-head experimental comparison"],
                    evidence_refs=refs,
                    mental_models_used=["Bayesian Thinking", "Decision Trees"],
                    hypothesis_ids=hyp_ids,
                )
            )

        if tradeoffs:
            t0 = tradeoffs[0]
            insights.append(
                ThoughtInsight(
                    statement=(
                        f"Core trade-off on {topic}: {t0.dimension_a} vs {t0.dimension_b}."
                    ),
                    why=f"Choose A when: {t0.choose_a_when}. Choose B when: {t0.choose_b_when}.",
                    why_now=opp_angle or "Opportunity framing makes the trade-off decision-relevant now.",
                    what_changes="Explicitly price the cost of each pole before committing.",
                    who_benefits="Leaders who make the trade-off visible",
                    who_loses="Stakeholders who wanted both poles without cost",
                    what_happens_next="Record the chosen pole and the kill-criteria for reversal.",
                    risks=[t0.cost_of_a, t0.cost_of_b],
                    what_is_missing=["Quantified cost of delay vs cost of error"],
                    evidence_refs=refs,
                    mental_models_used=["Opportunity Cost", "Expected Value"],
                    hypothesis_ids=hyp_ids,
                )
            )

        for insight in insights:
            self.confidence.score_insight(
                insight,
                claims,
                contradictions_count=0,
                hypotheses_count=len(hypotheses),
                counterarguments_count=len(counters),
                trends=trends,
            )
        return insights

    def run_packet(
        self,
        *,
        topic: str = "",
        evidence: Any = None,
        knowledge_graph: Any = None,
        research: Any = None,
        trends: Any = None,
        opportunity: Any = None,
    ) -> ReasoningPacket:
        research_d = extract_research(research)
        topic = topic_or_default(topic, research_d)
        # Evidence Graph is authoritative; research.evidence is supplemental
        claims = extract_claims(evidence)
        if not claims and research_d.get("evidence"):
            claims = extract_claims(research_d.get("evidence"))
        trend_list = extract_trends(trends if trends is not None else research_d.get("trends"))
        opp = extract_opportunity(opportunity)
        kg_meta = knowledge_summary(knowledge_graph)

        assumptions = self.extract_assumptions(topic, claims, research_d)
        contradictions = self.identify_contradictions(claims, knowledge_graph)
        hypotheses = self.hypotheses.generate(
            topic, claims, trends=trend_list, contradictions=contradictions
        )
        first = self.first_principles.analyze(topic, claims)
        models = self.mental_models.apply(topic, claims, limit=10)
        tradeoff_list = self.tradeoffs.analyze(topic, claims, opportunity=opp)
        frameworks = self.frameworks.build(
            topic, claims, hypotheses=hypotheses, tradeoffs=tradeoff_list
        )
        conclusions = [h.statement for h in hypotheses[:2]]
        if claims:
            conclusions.append(normalize_text(str(top_claims(claims, limit=1)[0].get("claim"))))
        counters = self.counters.challenge(conclusions, claims, hypotheses=hypotheses)
        causal_links = self.causal.infer(topic, claims, trends=trend_list)
        system_map = self.systems.map_system(topic, claims, knowledge_graph=knowledge_graph)
        analogies = self.analogies.generate(topic, claims)
        decision = self.decisions.decide(
            topic, claims, opportunity=opp, tradeoffs=tradeoff_list
        )
        scenarios = self.scenarios.simulate(
            topic, claims, trends=trend_list, decision=decision
        )
        insights = self.synthesize_insights(
            topic,
            claims=claims,
            hypotheses=hypotheses,
            mental_models=models,
            trends=trend_list,
            opportunity=opp,
            tradeoffs=tradeoff_list,
            counters=counters,
        )
        overall = self.confidence.score(
            claims,
            insights=insights,
            contradictions_count=len(contradictions),
            hypotheses_count=len(hypotheses),
            counterarguments_count=len(counters),
            trends=trend_list,
        )
        reflection = self.reflection.reflect(
            topic,
            claims=claims,
            insights=insights,
            contradictions=contradictions,
            counterarguments=counters,
            open_questions=list(research_d.get("open_questions") or []),
        )

        return ReasoningPacket(
            topic=topic,
            assumptions=assumptions,
            contradictions=contradictions,
            hypotheses=hypotheses,
            first_principles=first,
            mental_models=models,
            frameworks=frameworks,
            tradeoffs=tradeoff_list,
            counterarguments=counters,
            causal_links=causal_links,
            systems=system_map,
            analogies=analogies,
            decision=decision,
            scenarios=scenarios,
            insights=insights,
            reflection=reflection,
            overall_confidence=overall,
            evidence_claim_count=len(claims),
            knowledge_node_count=len(kg_meta.get("nodes") or []),
            meta={
                "deterministic": True,
                "hallucination_policy": "never_invent_facts",
                "evidence_required": True,
                "pipeline": [
                    "extract_assumptions",
                    "identify_contradictions",
                    "generate_hypotheses",
                    "first_principles",
                    "mental_models",
                    "frameworks",
                    "tradeoffs",
                    "counterarguments",
                    "insights",
                    "confidence",
                    "reflection",
                ],
            },
        )

    async def run(self, payload: ReasoningInput | dict[str, Any]) -> ReasoningOutput:
        if isinstance(payload, dict):
            topic = str(payload.get("topic") or "")
            extra = payload
            data = payload
        else:
            topic = payload.topic
            extra = payload.extra or {}
            data = payload.model_dump()

        packet = self.run_packet(
            topic=topic,
            evidence=extra.get("evidence") or data.get("evidence"),
            knowledge_graph=extra.get("knowledge_graph") or data.get("knowledge_graph"),
            research=extra.get("research") or data.get("research"),
            trends=extra.get("trends") or data.get("trends"),
            opportunity=extra.get("opportunity") or data.get("opportunity"),
        )
        # Compact thought text — not an article
        lines = [f"Thoughts on {packet.topic}:"]
        for insight in packet.insights:
            lines.append(f"- {insight.statement}")
        lines.append(f"Confidence: {packet.overall_confidence.confidence:.2f}")
        if packet.reflection.overlooked:
            lines.append(f"Overlooked: {packet.reflection.overlooked[0]}")

        return ReasoningOutput(
            text="\n".join(lines),
            packet=packet,
            data=packet.as_dict(),
            meta={"agent": self.name, "deterministic": True},
        )


# Public alias
ReasoningEngine = ReasoningPipeline
