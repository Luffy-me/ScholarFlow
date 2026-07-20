"""Research intelligence + connector tests."""

from __future__ import annotations

import pytest

from agents.research import ResearchOrchestrator, ResearchOrchestratorInput
from agents.research.collector import ResearchCollector
from agents.research.deduplicator import ResearchDeduplicator
from agents.research.evidence_extractor import EvidenceExtractor
from agents.research.source_ranker import SourceRanker
from agents.research.trend_detector import TrendDetector
from connectors.base import SourceDocument
from connectors.registry import get_connector, list_connectors, register_connector
from knowledge.evidence.store import EvidenceStore


@pytest.mark.asyncio
async def test_research_orchestration_offline(tmp_path) -> None:
    store = EvidenceStore(tmp_path / "evidence.json")
    orch = ResearchOrchestrator(evidence_store=store)
    result = await orch.run(ResearchOrchestratorInput(topic="local LLM evaluation"))
    assert result.brief is not None
    assert result.brief.sources
    assert result.brief.trends
    assert result.brief.evidence
    assert result.brief.summary
    assert store.list_claims()


@pytest.mark.asyncio
async def test_connector_normalization_and_confidence() -> None:
    assert "arxiv" in list_connectors()
    assert "official_docs" in list_connectors()
    connector = get_connector("github")
    docs = await connector.collect("RAG systems", limit=2)
    assert docs
    normalized = connector.normalize(docs[0])
    assert normalized["source_type"] == "github"
    assert normalized["tier"] == 1
    assert 0 < connector.confidence(docs[0]) <= 1


@pytest.mark.asyncio
async def test_collector_dedupe_rank_extract_trends() -> None:
    collector = ResearchCollector(["arxiv", "hackernews", "reddit"])
    docs = await collector.collect("vector databases", limit_per_source=2)
    # Inject duplicate
    docs.append(docs[0])
    unique = ResearchDeduplicator().dedupe(docs)
    assert len(unique) < len(docs)
    ranked = SourceRanker().rank(unique, query="vector databases")
    assert ranked[0].score >= ranked[-1].score
    evidence = EvidenceExtractor().extract(unique, ranked)
    assert evidence
    trends = TrendDetector().detect(unique, topic="vector databases")
    assert trends
    assert trends[0].source_count >= 1
    assert "trend" in trends[0].model_dump()


def test_register_future_connector_without_agent_changes() -> None:
    class Dummy:
        name = "exa"
        tier = 1

        async def collect(self, query: str, *, limit: int = 5):
            return [
                SourceDocument(
                    id="exa:1",
                    title=f"Exa hit for {query}",
                    source_type="exa",
                    tier=1,
                    confidence=0.9,
                )
            ]

        def normalize(self, document):
            return document.normalize()

        def confidence(self, document):
            return 0.9

    register_connector("exa", Dummy)
    assert "exa" in list_connectors()
    assert get_connector("exa").name == "exa"


def test_evidence_store_writer_allowed_claims(tmp_path) -> None:
    store = EvidenceStore(tmp_path / "ev.json")
    store.upsert(
        {
            "claim": "Evaluation loops matter more than model size",
            "supporting_sources": ["arxiv:1"],
            "confidence": 0.9,
            "verified": True,
        }
    )
    store.upsert(
        {
            "claim": "Some teams prefer larger models",
            "supporting_sources": ["reddit:1"],
            "confidence": 0.4,
            "verified": False,
        }
    )
    allowed = store.writer_allowed_claims()
    assert any(c["verified"] for c in allowed)
    assert any(c.get("attribution_required") for c in allowed)
