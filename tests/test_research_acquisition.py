"""Phase 5 — Research Acquisition Layer tests."""

from __future__ import annotations

import os
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

from acquisition import (
    IntelligenceScheduler,
    RSSRegistry,
    SourceRegistry,
    StorageManager,
    list_rss_categories,
    list_sources,
)
from acquisition.source_registry import SourceSpec
from connectors.base import SourceDocument
from connectors.registry import get_connector, list_connectors, register_connector


REQUIRED_CONNECTORS = [
    "rss",
    "github_trending",
    "github_releases",
    "arxiv",
    "paperswithcode",
    "semanticscholar",
    "openalex",
    "crossref",
    "hackernews",
    "reddit",
    "producthunt",
    "huggingface_models",
    "huggingface_papers",
    "openai_blog",
    "anthropic_blog",
    "deepmind_blog",
    "cloudflare_blog",
    "stripe_engineering",
    "vercel_blog",
    "linear_blog",
    "netflix_tech_blog",
    "uber_engineering",
    "shopify_engineering",
    "stackoverflow_blog",
    "devto",
    "medium",
    "hashnode",
]


CONTRACT_METHODS = [
    "collect",
    "normalize",
    "extract_metadata",
    "extract_entities",
    "extract_evidence",
    "calculate_confidence",
    "deduplicate",
]


@pytest.fixture(autouse=True)
def _force_offline(monkeypatch):
    monkeypatch.setenv("ACQUISITION_OFFLINE", "1")


def test_required_connectors_registered() -> None:
    names = set(list_connectors())
    missing = [n for n in REQUIRED_CONNECTORS if n not in names]
    assert not missing, f"missing connectors: {missing}"


@pytest.mark.asyncio
@pytest.mark.parametrize("name", REQUIRED_CONNECTORS)
async def test_connector_acquisition_contract(name: str) -> None:
    connector = get_connector(name)
    for method in CONTRACT_METHODS:
        assert hasattr(connector, method), f"{name} missing {method}"
    docs = await connector.collect("evaluation systems", limit=2)
    assert docs
    doc = docs[0]
    normalized = connector.normalize(doc)
    assert normalized["title"]
    assert connector.extract_metadata(doc)
    assert isinstance(connector.extract_entities(doc), list)
    evidence = connector.extract_evidence(doc)
    assert evidence
    assert 0 < connector.calculate_confidence(doc) <= 1
    deduped = connector.deduplicate(docs + docs)
    assert len(deduped) == len(docs)


def test_source_registry_fields() -> None:
    registry = SourceRegistry()
    assert "arxiv" in list_sources()
    spec = registry.get("arxiv")
    assert 0 < spec.authority_score <= 1
    assert 0 < spec.freshness_weight <= 1
    assert spec.update_frequency
    assert spec.category
    assert spec.trust_level in {"high", "medium", "low"}
    assert spec.parser == "arxiv"
    connector = registry.resolve_parser("arxiv")
    assert connector.name == "arxiv"


def test_source_registry_hot_register() -> None:
    registry = SourceRegistry()

    class FutureConnector:
        name = "exa_future"
        tier = 1

        async def collect(self, query: str, *, limit: int = 5):
            return [
                SourceDocument(
                    id="exa_future:1",
                    title=f"hit {query}",
                    source_type="exa_future",
                    tier=1,
                )
            ]

        def normalize(self, document):
            return document.normalize()

        def extract_metadata(self, document):
            return {"connector": self.name}

        def extract_entities(self, document):
            return []

        def extract_evidence(self, document):
            return []

        def calculate_confidence(self, document):
            return 0.9

        def deduplicate(self, documents):
            return documents

    registry.register(
        SourceSpec(
            name="exa_future",
            authority_score=0.8,
            freshness_weight=0.9,
            update_frequency="hourly",
            category="ai",
            trust_level="medium",
            parser="exa_future",
            tier=1,
        ),
        factory=FutureConnector,
    )
    assert "exa_future" in registry.list_names()
    assert get_connector("exa_future").name == "exa_future"


def test_rss_registry_categories() -> None:
    registry = RSSRegistry()
    cats = list_rss_categories()
    expected = {
        "AI",
        "Machine Learning",
        "Economics",
        "Finance",
        "Business",
        "Programming",
        "Open Source",
        "Cybersecurity",
        "Cloud",
        "Startups",
    }
    assert expected.issubset(set(cats))
    for cat in expected:
        assert registry.by_category(cat), f"no feeds for {cat}"
    assert len(registry.all_feeds()) >= 30


def test_storage_manager_cache_and_cleanup(tmp_path: Path) -> None:
    storage = StorageManager(tmp_path / "acq")
    storage.write_research_cache("arxiv", "rag", {"documents": [{"title": "x"}]})
    assert storage.read_research_cache("arxiv", "rag") is not None
    raw = storage.store_raw_download("sample", "hello world", suffix=".txt")
    assert raw.exists()
    # age the file beyond 24h
    old = datetime.now(timezone.utc) - timedelta(hours=25)
    os.utime(raw, (old.timestamp(), old.timestamp()))
    removed = storage.cleanup_raw_downloads(max_age_hours=24)
    assert removed >= 1
    assert not raw.exists()
    knowledge = storage.write_knowledge("note", {"ok": True})
    assert knowledge.exists()
    backup = storage.backup_to_google_drive(drive_mirror_dir=tmp_path / "gdrive")
    assert backup["ok"] is True
    assert Path(backup["drive_path"]).exists()


@pytest.mark.asyncio
async def test_intelligence_scheduler_run_once(tmp_path: Path) -> None:
    storage = StorageManager(tmp_path / "acq")
    sched = IntelligenceScheduler(
        topics=["local LLM evaluation"],
        sources=["arxiv", "hackernews", "openai_blog"],
        storage=storage,
        interval_seconds=60,
        raw_max_age_hours=24,
    )
    result = await sched.run_once(include_rss=True)
    assert result["documents"] >= 1
    assert result["claims"] >= 1
    assert result["knowledge_nodes"] >= 1
    assert "cleanup" in result
    assert (storage.knowledge_dir / "scheduler_last_run.json").exists()
    assert sched.evidence_store.list_claims()
    assert sched.knowledge_graph.nodes()
