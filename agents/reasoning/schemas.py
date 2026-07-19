"""Schemas for the ScholarFlow Reasoning Engine (deterministic thoughts, not articles)."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field

from agents.base import AgentInput, AgentOutput


class Assumption(BaseModel):
    statement: str
    source_refs: list[str] = Field(default_factory=list)
    risk_if_wrong: str = ""


class Contradiction(BaseModel):
    claim_a: str
    claim_b: str
    source_refs: list[str] = Field(default_factory=list)
    tension: str = ""


class Hypothesis(BaseModel):
    id: str
    statement: str
    rationale: str = ""
    competing_with: list[str] = Field(default_factory=list)
    evidence_refs: list[str] = Field(default_factory=list)
    confidence: float = 0.0


class FirstPrinciplesBreakdown(BaseModel):
    problem: str
    fundamentals: list[str] = Field(default_factory=list)
    derived_implications: list[str] = Field(default_factory=list)
    evidence_refs: list[str] = Field(default_factory=list)


class MentalModelApplication(BaseModel):
    model: str
    lens: str
    observation: str
    implication: str
    evidence_refs: list[str] = Field(default_factory=list)


class Framework(BaseModel):
    name: str
    kind: str
    steps: list[str] = Field(default_factory=list)
    description: str = ""
    reusable: bool = True
    evidence_refs: list[str] = Field(default_factory=list)


class Tradeoff(BaseModel):
    dimension_a: str
    dimension_b: str
    choose_a_when: str = ""
    choose_b_when: str = ""
    cost_of_a: str = ""
    cost_of_b: str = ""
    evidence_refs: list[str] = Field(default_factory=list)


class CounterArgument(BaseModel):
    target_conclusion: str
    reasons_it_may_be_wrong: list[str] = Field(default_factory=list)
    missing_evidence: list[str] = Field(default_factory=list)
    alternative_explanations: list[str] = Field(default_factory=list)
    evidence_refs: list[str] = Field(default_factory=list)


class CausalLink(BaseModel):
    cause: str
    effect: str
    mechanism: str = ""
    evidence_refs: list[str] = Field(default_factory=list)
    confidence: float = 0.0


class SystemMap(BaseModel):
    stocks: list[str] = Field(default_factory=list)
    flows: list[str] = Field(default_factory=list)
    feedback_loops: list[str] = Field(default_factory=list)
    leverage_points: list[str] = Field(default_factory=list)
    evidence_refs: list[str] = Field(default_factory=list)


class Analogy(BaseModel):
    source_domain: str
    target_domain: str
    mapping: str
    caution: str = ""
    evidence_refs: list[str] = Field(default_factory=list)


class DecisionOption(BaseModel):
    option: str
    expected_value_note: str = ""
    risks: list[str] = Field(default_factory=list)
    upside: list[str] = Field(default_factory=list)
    evidence_refs: list[str] = Field(default_factory=list)


class DecisionRecommendation(BaseModel):
    question: str
    options: list[DecisionOption] = Field(default_factory=list)
    recommended: str = ""
    decision_rule: str = ""
    evidence_refs: list[str] = Field(default_factory=list)


class Scenario(BaseModel):
    label: str  # best | expected | worst
    narrative: str
    triggers: list[str] = Field(default_factory=list)
    outcomes: list[str] = Field(default_factory=list)
    evidence_refs: list[str] = Field(default_factory=list)


class ConfidenceScore(BaseModel):
    evidence_quality: float = 0.0
    reasoning_quality: float = 0.0
    novelty: float = 0.0
    confidence: float = 0.0
    notes: list[str] = Field(default_factory=list)


class ThoughtInsight(BaseModel):
    """A structured thought — not an article."""

    statement: str
    why: str = ""
    why_now: str = ""
    what_changes: str = ""
    who_benefits: str = ""
    who_loses: str = ""
    what_happens_next: str = ""
    risks: list[str] = Field(default_factory=list)
    what_is_missing: list[str] = Field(default_factory=list)
    evidence_refs: list[str] = Field(default_factory=list)
    mental_models_used: list[str] = Field(default_factory=list)
    hypothesis_ids: list[str] = Field(default_factory=list)
    confidence: ConfidenceScore = Field(default_factory=ConfidenceScore)


class ReflectionResult(BaseModel):
    overlooked: list[str] = Field(default_factory=list)
    questions_raised: list[str] = Field(default_factory=list)
    tightened_conclusions: list[str] = Field(default_factory=list)


class ReasoningPacket(BaseModel):
    """Full deterministic reasoning output."""

    topic: str
    assumptions: list[Assumption] = Field(default_factory=list)
    contradictions: list[Contradiction] = Field(default_factory=list)
    hypotheses: list[Hypothesis] = Field(default_factory=list)
    first_principles: FirstPrinciplesBreakdown = Field(default_factory=FirstPrinciplesBreakdown)
    mental_models: list[MentalModelApplication] = Field(default_factory=list)
    frameworks: list[Framework] = Field(default_factory=list)
    tradeoffs: list[Tradeoff] = Field(default_factory=list)
    counterarguments: list[CounterArgument] = Field(default_factory=list)
    causal_links: list[CausalLink] = Field(default_factory=list)
    systems: SystemMap = Field(default_factory=SystemMap)
    analogies: list[Analogy] = Field(default_factory=list)
    decision: DecisionRecommendation = Field(default_factory=DecisionRecommendation)
    scenarios: list[Scenario] = Field(default_factory=list)
    insights: list[ThoughtInsight] = Field(default_factory=list)
    reflection: ReflectionResult = Field(default_factory=ReflectionResult)
    overall_confidence: ConfidenceScore = Field(default_factory=ConfidenceScore)
    evidence_claim_count: int = 0
    knowledge_node_count: int = 0
    meta: dict[str, Any] = Field(default_factory=dict)

    def as_dict(self) -> dict[str, Any]:
        return self.model_dump()


class ReasoningInput(AgentInput):
    """Inputs: KG, evidence, research, trends, opportunity — all optional dict payloads."""

    pass


class ReasoningOutput(AgentOutput):
    packet: ReasoningPacket = Field(default_factory=ReasoningPacket)

    def as_thoughts(self) -> dict[str, Any]:
        return self.packet.as_dict()
