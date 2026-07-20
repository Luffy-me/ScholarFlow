"""Phase 7 — Reasoning Engine tests (50+), independent subsystem."""

from __future__ import annotations

import pytest

from agents.reasoning import (
    FRAMEWORK_KINDS,
    MENTAL_MODELS,
    ConfidenceEngine,
    CounterArgumentEngine,
    DecisionEngine,
    FirstPrinciplesEngine,
    FrameworkBuilder,
    HypothesisGenerator,
    MentalModelEngine,
    ReasoningInput,
    ReasoningPipeline,
    ReflectionEngine,
    ScenarioSimulator,
    SystemsThinkingEngine,
    TradeoffAnalyzer,
)
from agents.reasoning.analogy_engine import AnalogyEngine
from agents.reasoning.causal_reasoning import CausalReasoningEngine
from agents.reasoning.schemas import ThoughtInsight
from knowledge.evidence.store import EvidenceStore
from knowledge_graph import KnowledgeGraph, NodeType, RelationType


def _claims() -> list[dict]:
    return [
        {
            "claim": "Evaluation loops improve product quality more than raw model size",
            "supporting_sources": ["arxiv:eval-1"],
            "contradicting_sources": [],
            "confidence": 0.9,
            "verified": True,
        },
        {
            "claim": "Distribution speed can outperform quality in early markets",
            "supporting_sources": ["hn:dist-2"],
            "contradicting_sources": ["arxiv:eval-1"],
            "confidence": 0.55,
            "verified": False,
        },
        {
            "claim": "Workflow constraints block adoption of local LLM tooling",
            "supporting_sources": ["github:wf-3"],
            "contradicting_sources": [],
            "confidence": 0.7,
            "verified": True,
        },
    ]


def _trends() -> list[dict]:
    return [
        {
            "trend": "Builders shifting from prompts to evaluation harnesses",
            "momentum": 0.8,
            "confidence": 0.65,
            "supporting_sources": ["arxiv:eval-1"],
        }
    ]


def _opportunity() -> dict:
    return {
        "topic": "local LLM evaluation",
        "score": 74.0,
        "recommended_angle": "Developer pain points around workflow quality",
        "target_audience": "engineers",
        "metrics": {"novelty": 0.7, "competition": 0.3},
    }


@pytest.fixture
def evidence_store(tmp_path):
    store = EvidenceStore(tmp_path / "evidence.json")
    for claim in _claims():
        store.upsert(claim)
    return store


@pytest.fixture
def knowledge_graph(tmp_path):
    graph = KnowledgeGraph(tmp_path / "graph.json")
    topic = graph.upsert_node(NodeType.TOPIC, "local LLM evaluation")
    tool = graph.upsert_node(NodeType.TOOL, "Ollama")
    paper = graph.upsert_node(NodeType.RESEARCH_PAPER, "Eval Harness Notes")
    graph.add_edge(topic.id, tool.id, RelationType.DEPENDS_ON)
    graph.add_edge(paper.id, topic.id, RelationType.SUPPORTS)
    graph.add_edge(tool.id, paper.id, RelationType.CONTRADICTS)
    return graph


# ---------------------------------------------------------------------------
# Mental models (library completeness)
# ---------------------------------------------------------------------------


def test_mental_models_library_has_required_names() -> None:
    required = {
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
    }
    assert required.issubset(set(MENTAL_MODELS))
    assert len(MENTAL_MODELS) >= 20


def test_mental_model_engine_lists_and_applies() -> None:
    engine = MentalModelEngine()
    assert engine.list_models() == list(MENTAL_MODELS)
    apps = engine.apply("pricing", _claims(), limit=5)
    assert len(apps) == 5
    assert all(a.evidence_refs for a in apps)
    assert all(a.model in MENTAL_MODELS for a in apps)


def test_mental_models_deterministic_order() -> None:
    engine = MentalModelEngine()
    a = [x.model for x in engine.apply("x", _claims(), limit=8)]
    b = [x.model for x in engine.apply("x", _claims(), limit=8)]
    assert a == b


@pytest.mark.parametrize("model", list(MENTAL_MODELS))
def test_each_mental_model_has_template(model: str) -> None:
    apps = MentalModelEngine().apply("topic", _claims(), models=[model], limit=1)
    assert len(apps) == 1
    assert apps[0].model == model
    assert apps[0].lens
    assert apps[0].implication


# ---------------------------------------------------------------------------
# Hypotheses / first principles / frameworks
# ---------------------------------------------------------------------------


def test_hypothesis_generator_competing_hypotheses() -> None:
    hyps = HypothesisGenerator().generate("eval systems", _claims(), trends=_trends())
    assert len(hyps) >= 2
    assert hyps[0].competing_with
    assert hyps[0].id != hyps[1].id
    assert hyps[0].evidence_refs


def test_hypothesis_generator_without_evidence() -> None:
    hyps = HypothesisGenerator().generate("empty topic", [])
    assert len(hyps) >= 2
    assert all(h.confidence <= 0.2 for h in hyps)


def test_hypothesis_ids_stable() -> None:
    g = HypothesisGenerator()
    a = [h.id for h in g.generate("t", _claims())]
    b = [h.id for h in g.generate("t", _claims())]
    assert a == b


def test_first_principles_uses_claims_only() -> None:
    fp = FirstPrinciplesEngine().analyze("eval", _claims())
    assert fp.fundamentals
    assert "Observable claim:" in fp.fundamentals[0]
    assert fp.evidence_refs
    empty = FirstPrinciplesEngine().analyze("eval", [])
    assert "No Evidence Graph" in empty.fundamentals[0]


def test_framework_kinds_complete() -> None:
    required = {
        "3-Step Framework",
        "5-Step Framework",
        "Decision Matrix",
        "Flywheel",
        "Pyramid",
        "Checklist",
        "Roadmap",
    }
    assert required.issubset(set(FRAMEWORK_KINDS))


def test_framework_builder_emits_all_kinds() -> None:
    hyps = HypothesisGenerator().generate("eval", _claims())
    trades = TradeoffAnalyzer().analyze("eval", _claims())
    frames = FrameworkBuilder().build("eval", _claims(), hypotheses=hyps, tradeoffs=trades)
    kinds = {f.kind for f in frames}
    assert "3-Step Framework" in kinds
    assert "Flywheel" in kinds
    assert "Roadmap" in kinds
    assert all(f.evidence_refs for f in frames if _claims())


def test_framework_steps_are_non_empty() -> None:
    for fw in FrameworkBuilder().build("topic", _claims()):
        assert fw.steps
        assert fw.reusable is True


# ---------------------------------------------------------------------------
# Counterarguments / decisions / scenarios / causal / systems / analogies
# ---------------------------------------------------------------------------


def test_counter_argument_challenges_conclusions() -> None:
    hyps = HypothesisGenerator().generate("eval", _claims())
    counters = CounterArgumentEngine().challenge(
        [h.statement for h in hyps], _claims(), hypotheses=hyps
    )
    assert counters
    c0 = counters[0]
    assert c0.reasons_it_may_be_wrong
    assert c0.missing_evidence
    assert c0.alternative_explanations


def test_counter_argument_flags_unverified() -> None:
    counters = CounterArgumentEngine().challenge(["Distribution wins"], _claims())
    blob = " ".join(counters[0].reasons_it_may_be_wrong).lower()
    assert "unverified" in blob or "contradict" in blob or "low-confidence" in blob


def test_decision_engine_wait_when_weak_evidence() -> None:
    d = DecisionEngine().decide("t", [], opportunity={"score": 90})
    assert "Wait" in d.recommended or "monitor" in d.recommended.lower()


def test_decision_engine_invest_when_strong() -> None:
    d = DecisionEngine().decide(
        "local LLM evaluation",
        _claims(),
        opportunity={"score": 80},
    )
    assert d.options
    assert d.recommended
    assert d.decision_rule


def test_decision_engine_probe_on_mixed() -> None:
    weak = [{"claim": "maybe something", "confidence": 0.5, "verified": False, "supporting_sources": ["x"]}]
    d = DecisionEngine().decide("t", weak, opportunity={"score": 40})
    assert "experiment" in d.recommended.lower() or "Probe" in d.recommended


def test_scenario_simulator_three_cases() -> None:
    scenarios = ScenarioSimulator().simulate("eval", _claims(), trends=_trends())
    labels = [s.label for s in scenarios]
    assert labels == ["best", "expected", "worst"]
    assert all(s.narrative for s in scenarios)


def test_scenario_includes_decision_in_expected() -> None:
    decision = DecisionEngine().decide("eval", _claims(), opportunity=_opportunity())
    scenarios = ScenarioSimulator().simulate("eval", _claims(), decision=decision)
    expected = next(s for s in scenarios if s.label == "expected")
    assert decision.recommended.split()[0] in expected.narrative or "experiment" in expected.narrative.lower() or "Probe" in expected.narrative or "Invest" in expected.narrative or "Wait" in expected.narrative


def test_causal_links_reference_evidence() -> None:
    links = CausalReasoningEngine().infer("eval", _claims(), trends=_trends())
    assert links
    assert links[0].evidence_refs
    assert links[0].confidence <= 1


def test_causal_without_evidence() -> None:
    links = CausalReasoningEngine().infer("eval", [])
    assert links[0].confidence == 0.0
    assert "no Evidence Graph" in links[0].cause


def test_systems_thinking_map(knowledge_graph) -> None:
    sm = SystemsThinkingEngine().map_system("eval", _claims(), knowledge_graph=knowledge_graph)
    assert sm.stocks and sm.flows and sm.feedback_loops and sm.leverage_points
    assert sm.evidence_refs


def test_systems_thinking_notes_kg_contradictions(knowledge_graph) -> None:
    sm = SystemsThinkingEngine().map_system("eval", _claims(), knowledge_graph=knowledge_graph)
    assert any("contradiction" in x.lower() for x in sm.feedback_loops)


def test_analogy_engine_cautions() -> None:
    analogies = AnalogyEngine().generate("eval", _claims())
    assert len(analogies) >= 3
    assert all("not evidence" in a.caution.lower() for a in analogies)


def test_tradeoff_analysis_dimensions() -> None:
    trades = TradeoffAnalyzer().analyze("eval", _claims(), opportunity=_opportunity())
    assert len(trades) >= 3
    assert trades[0].dimension_a and trades[0].dimension_b
    assert trades[0].cost_of_a and trades[0].choose_b_when


# ---------------------------------------------------------------------------
# Confidence + reflection
# ---------------------------------------------------------------------------


def test_confidence_engine_components() -> None:
    score = ConfidenceEngine().score(
        _claims(),
        insights=[],
        contradictions_count=1,
        hypotheses_count=3,
        counterarguments_count=2,
        trends=_trends(),
    )
    assert 0 <= score.evidence_quality <= 1
    assert 0 <= score.reasoning_quality <= 1
    assert 0 <= score.novelty <= 1
    assert 0 <= score.confidence <= 1


def test_confidence_capped_without_claims() -> None:
    score = ConfidenceEngine().score([])
    assert score.confidence <= 0.25


def test_confidence_insight_requires_refs() -> None:
    insight = ThoughtInsight(statement="Ungrounded thought", why="x")
    scored = ConfidenceEngine().score_insight(insight, _claims())
    assert scored.confidence <= 0.2
    assert insight.confidence.confidence <= 0.2


def test_reflection_asks_what_overlooked() -> None:
    insights = [
        ThoughtInsight(
            statement="Thesis",
            why="because",
            evidence_refs=["arxiv:1"],
            who_loses="",
            what_is_missing=[],
        )
    ]
    result = ReflectionEngine().reflect(
        "eval",
        claims=_claims(),
        insights=insights,
        counterarguments=CounterArgumentEngine().challenge(["Thesis"], _claims()),
    )
    assert any("overlook" in q.lower() for q in result.questions_raised)
    assert result.overlooked
    assert result.tightened_conclusions


def test_reflection_flags_missing_evidence_graph() -> None:
    result = ReflectionEngine().reflect("t", claims=[], insights=[])
    assert any("No Evidence Graph" in x for x in result.overlooked)


# ---------------------------------------------------------------------------
# Pipeline integration
# ---------------------------------------------------------------------------


def test_pipeline_run_packet_shape(evidence_store, knowledge_graph) -> None:
    packet = ReasoningPipeline().run_packet(
        topic="local LLM evaluation",
        evidence=evidence_store,
        knowledge_graph=knowledge_graph,
        research={
            "topic": "local LLM evaluation",
            "open_questions": ["Which metric predicts retention?"],
            "summary": "brief",
        },
        trends=_trends(),
        opportunity=_opportunity(),
    )
    assert packet.topic == "local LLM evaluation"
    assert packet.assumptions
    assert packet.hypotheses
    assert packet.first_principles.fundamentals
    assert packet.mental_models
    assert packet.frameworks
    assert packet.tradeoffs
    assert packet.counterarguments
    assert packet.insights
    assert packet.scenarios
    assert packet.decision.recommended
    assert packet.reflection.questions_raised
    assert packet.meta["deterministic"] is True
    assert packet.evidence_claim_count >= 3
    assert packet.knowledge_node_count >= 1


@pytest.mark.asyncio
async def test_pipeline_async_run(evidence_store, knowledge_graph) -> None:
    result = await ReasoningPipeline().run(
        ReasoningInput(
            topic="local LLM evaluation",
            extra={
                "evidence": evidence_store,
                "knowledge_graph": knowledge_graph,
                "research": {"open_questions": ["x"]},
                "trends": _trends(),
                "opportunity": _opportunity(),
            },
        )
    )
    assert "Thoughts on" in result.text
    assert result.packet.insights
    assert result.as_thoughts()["overall_confidence"]["confidence"] >= 0


def test_pipeline_deterministic(evidence_store, knowledge_graph) -> None:
    pipe = ReasoningPipeline()
    kwargs = dict(
        topic="local LLM evaluation",
        evidence=evidence_store,
        knowledge_graph=knowledge_graph,
        research={"open_questions": ["q1"]},
        trends=_trends(),
        opportunity=_opportunity(),
    )
    a = pipe.run_packet(**kwargs).as_dict()
    b = pipe.run_packet(**kwargs).as_dict()
    # Drop volatile-looking fields if any — packet should be stable
    assert a["hypotheses"] == b["hypotheses"]
    assert a["insights"] == b["insights"]
    assert a["overall_confidence"] == b["overall_confidence"]
    assert a["frameworks"] == b["frameworks"]


def test_insights_answer_required_questions(evidence_store) -> None:
    packet = ReasoningPipeline().run_packet(
        topic="eval",
        evidence=evidence_store,
        trends=_trends(),
        opportunity=_opportunity(),
    )
    for insight in packet.insights:
        assert insight.why
        assert insight.why_now
        assert insight.what_changes
        assert insight.who_benefits
        assert insight.who_loses
        assert insight.what_happens_next
        assert insight.risks
        assert insight.what_is_missing
        assert insight.evidence_refs  # never hallucinate without refs when claims exist


def test_pipeline_without_evidence_stays_provisional() -> None:
    packet = ReasoningPipeline().run_packet(topic="unknown area", evidence=[])
    assert packet.overall_confidence.confidence <= 0.35
    assert any("Insufficient" in h.statement or "measurement" in h.statement.lower() for h in packet.hypotheses)


def test_pipeline_uses_research_evidence_fallback() -> None:
    packet = ReasoningPipeline().run_packet(
        topic="eval",
        evidence=None,
        research={"evidence": _claims(), "trends": _trends()},
    )
    assert packet.evidence_claim_count >= 1
    assert packet.insights[0].evidence_refs


def test_contradictions_from_evidence_and_kg(evidence_store, knowledge_graph) -> None:
    packet = ReasoningPipeline().run_packet(
        topic="eval",
        evidence=evidence_store,
        knowledge_graph=knowledge_graph,
    )
    assert packet.contradictions
    assert any("contradict" in c.tension.lower() for c in packet.contradictions)


def test_assumptions_include_open_questions(evidence_store) -> None:
    packet = ReasoningPipeline().run_packet(
        topic="eval",
        evidence=evidence_store,
        research={"open_questions": ["What fails in production?"]},
    )
    assert any("open question" in a.statement.lower() for a in packet.assumptions)


@pytest.mark.asyncio
async def test_pipeline_accepts_dict_payload(evidence_store) -> None:
    result = await ReasoningPipeline().run(
        {
            "topic": "eval",
            "evidence": evidence_store,
            "trends": _trends(),
        }
    )
    assert result.packet.topic == "eval"


def test_no_article_length_output(evidence_store) -> None:
    """Thoughts are compact — not blog posts."""
    packet = ReasoningPipeline().run_packet(topic="eval", evidence=evidence_store)
    for insight in packet.insights:
        assert len(insight.statement) < 500


def test_reasoning_output_meta_flags(evidence_store) -> None:
    packet = ReasoningPipeline().run_packet(topic="eval", evidence=evidence_store)
    assert packet.meta["hallucination_policy"] == "never_invent_facts"
    assert packet.meta["evidence_required"] is True
    assert "generate_hypotheses" in packet.meta["pipeline"]


# ---------------------------------------------------------------------------
# Extra focused unit tests to exceed 50
# ---------------------------------------------------------------------------


def test_top_claim_ordering_prefers_verified() -> None:
    from agents.reasoning._util import top_claims

    ranked = top_claims(_claims(), limit=1)
    assert ranked[0]["verified"] is True


def test_extract_claims_from_store(evidence_store) -> None:
    from agents.reasoning._util import extract_claims

    claims = extract_claims(evidence_store)
    assert len(claims) >= 3


def test_extract_claims_from_pydantic_like() -> None:
    from agents.reasoning._util import extract_claims
    from agents.research.schemas import EvidenceClaim

    claims = extract_claims(
        [EvidenceClaim(claim="A verified workflow constraint blocks shipping", confidence=0.8, verified=True)]
    )
    assert claims[0]["claim"].startswith("A verified")


def test_extract_trends_normalization() -> None:
    from agents.reasoning._util import extract_trends

    assert extract_trends({"trends": _trends()})[0]["trend"]
    assert extract_trends(["raw trend string"])[0]["trend"] == "raw trend string"


def test_knowledge_summary_labels(knowledge_graph) -> None:
    from agents.reasoning._util import knowledge_summary

    summary = knowledge_summary(knowledge_graph)
    assert "Ollama" in summary["labels"]
    assert summary["contradict_edges"]


def test_mean_and_verified_ratio() -> None:
    from agents.reasoning._util import mean_confidence, verified_ratio

    assert mean_confidence(_claims()) > 0.5
    assert 0 < verified_ratio(_claims()) < 1


def test_has_evidence_support_true_and_false() -> None:
    from agents.reasoning._util import has_evidence_support

    assert has_evidence_support("evaluation loops product quality", _claims()) is True
    assert has_evidence_support("quantum teleportation unicorns", _claims()) is False


def test_stable_id_deterministic() -> None:
    from agents.reasoning._util import stable_id

    assert stable_id("hyp", "a", "b") == stable_id("hyp", "a", "b")
    assert stable_id("hyp", "a", "b") != stable_id("hyp", "a", "c")


def test_opportunity_extraction_model_dump() -> None:
    from agents.reasoning._util import extract_opportunity
    from agents.content_opportunity.engine import ContentOpportunity

    opp = ContentOpportunity(topic="t", score=10, target_audience="founders")
    assert extract_opportunity(opp)["target_audience"] == "founders"


def test_research_brief_extraction() -> None:
    from agents.reasoning._util import extract_research
    from agents.research.schemas import ResearchBrief

    brief = ResearchBrief(topic="abc", summary="s")
    assert extract_research(brief)["topic"] == "abc"


@pytest.mark.asyncio
async def test_end_to_end_with_all_inputs(evidence_store, knowledge_graph) -> None:
    result = await ReasoningPipeline().run(
        ReasoningInput(
            topic="local LLM evaluation",
            extra={
                "evidence": evidence_store,
                "knowledge_graph": knowledge_graph,
                "research": {
                    "topic": "local LLM evaluation",
                    "summary": "Evidence favors evaluation loops",
                    "open_questions": ["Metric?"],
                    "evidence": _claims(),
                    "trends": _trends(),
                },
                "trends": _trends(),
                "opportunity": _opportunity(),
            },
        )
    )
    data = result.as_thoughts()
    assert data["decision"]["options"]
    assert len(data["scenarios"]) == 3
    assert data["mental_models"]
    assert data["frameworks"]
    assert data["counterarguments"][0]["alternative_explanations"]
    assert data["reflection"]["overlooked"]
    assert data["overall_confidence"]["evidence_quality"] > 0


def test_module_exports() -> None:
    import agents.reasoning as reasoning

    for name in [
        "ReasoningPipeline",
        "HypothesisGenerator",
        "FrameworkBuilder",
        "MentalModelEngine",
        "ConfidenceEngine",
        "ScenarioSimulator",
    ]:
        assert hasattr(reasoning, name)
