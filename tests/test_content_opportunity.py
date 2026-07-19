"""Content opportunity engine tests."""

from __future__ import annotations

import pytest

from agents.content_opportunity import ContentOpportunityEngine
from agents.research import ResearchOrchestrator, ResearchOrchestratorInput
from knowledge.evidence.store import EvidenceStore


@pytest.mark.asyncio
async def test_opportunity_scores_specific_topic_higher_than_generic(tmp_path) -> None:
    store = EvidenceStore(tmp_path / "e.json")
    orch = ResearchOrchestrator(evidence_store=store)
    brief = (await orch.run(ResearchOrchestratorInput(topic="local LLM evaluation loops"))).brief
    engine = ContentOpportunityEngine()
    specific = engine.score_topic("local LLM evaluation loops", brief=brief, audience="engineers")
    generic = engine.score_topic("AI", audience="everyone")
    assert specific.score > generic.score
    assert specific.recommended_angle
    assert specific.target_audience
    assert "novelty" in specific.metrics


def test_opportunity_rank_orders_topics() -> None:
    engine = ContentOpportunityEngine()
    ranked = engine.rank(
        ["AI", "RAG evaluation harness design", "digital transformation"],
        audience="founders",
    )
    assert ranked[0].topic != "AI"
    assert ranked[0].score >= ranked[-1].score
