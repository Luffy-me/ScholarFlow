"""Intelligence Scheduler — download, process evidence, update KG, cleanup."""

from __future__ import annotations

import asyncio
import json
import threading
from datetime import datetime, timezone
from typing import Any

from acquisition.rss_registry import RSSRegistry
from acquisition.source_registry import SourceRegistry
from acquisition.storage import StorageManager
from connectors.base import SourceDocument
from connectors.http_utils import fetch_text, parse_rss_items
from connectors.real_base import docs_from_rss_items
from knowledge.evidence.store import EvidenceStore
from knowledge_graph import KnowledgeGraph
from knowledge_graph.schema import NodeType, RelationType


class IntelligenceScheduler:
    """Runs acquisition cycles locally without UI or cloud dependency."""

    def __init__(
        self,
        *,
        topics: list[str] | None = None,
        sources: list[str] | None = None,
        storage: StorageManager | None = None,
        source_registry: SourceRegistry | None = None,
        rss_registry: RSSRegistry | None = None,
        evidence_store: EvidenceStore | None = None,
        knowledge_graph: KnowledgeGraph | None = None,
        interval_seconds: float = 3600,
        raw_max_age_hours: float = 24,
    ) -> None:
        self.topics = topics or ["artificial intelligence", "machine learning systems"]
        self.sources = sources
        self.storage = storage or StorageManager()
        self.source_registry = source_registry or SourceRegistry()
        self.rss_registry = rss_registry or RSSRegistry()
        self.evidence_store = evidence_store or EvidenceStore(
            self.storage.knowledge_dir / "evidence_graph.json"
        )
        self.knowledge_graph = knowledge_graph or KnowledgeGraph(
            self.storage.knowledge_dir / "graph.json"
        )
        self.interval_seconds = interval_seconds
        self.raw_max_age_hours = raw_max_age_hours
        self._stop = threading.Event()
        self._thread: threading.Thread | None = None
        self.last_run: dict[str, Any] | None = None

    def selected_sources(self) -> list[str]:
        if self.sources:
            return list(self.sources)
        # Prefer high-signal defaults for automatic runs
        preferred = [
            "arxiv",
            "hackernews",
            "github_trending",
            "huggingface_papers",
            "openai_blog",
            "anthropic_blog",
            "reddit",
            "devto",
            "rss",
        ]
        available = set(self.source_registry.enabled_parsers())
        return [s for s in preferred if s in available] or sorted(available)[:8]

    async def collect_from_sources(self, topic: str, *, limit: int = 3) -> list[SourceDocument]:
        docs: list[SourceDocument] = []
        for name in self.selected_sources():
            cached = self.storage.read_research_cache(name, topic)
            if cached and isinstance(cached.get("documents"), list):
                for row in cached["documents"]:
                    docs.append(SourceDocument(**{k: v for k, v in row.items() if k in SourceDocument.__dataclass_fields__}))
                continue
            try:
                connector = self.source_registry.resolve_parser(name)
            except KeyError:
                continue
            try:
                collected = await connector.collect(topic, limit=limit)
            except Exception:  # noqa: BLE001
                continue
            collected = connector.deduplicate(collected)
            serializable = [connector.normalize(d) for d in collected]
            self.storage.write_research_cache(
                name,
                topic,
                {"documents": [d.__dict__ for d in collected], "normalized": serializable},
            )
            # Persist a raw snapshot for 24h retention policy
            self.storage.store_raw_download(
                f"{name}_{topic}",
                json.dumps(serializable, ensure_ascii=False),
                suffix=".json",
            )
            docs.extend(collected)
        return docs

    async def collect_rss_category(self, category: str, *, limit_per_feed: int = 3) -> list[SourceDocument]:
        docs: list[SourceDocument] = []
        for feed in self.rss_registry.by_category(category):
            xml = await fetch_text(feed.url)
            if xml:
                self.storage.store_raw_download(feed.name, xml, suffix=".xml")
                items = parse_rss_items(xml, limit=limit_per_feed)
                docs.extend(
                    docs_from_rss_items(
                        items,
                        connector="rss",
                        tier=2,
                        query=category,
                    )
                )
            else:
                # Offline-friendly stub when network disabled
                docs.append(
                    SourceDocument(
                        id=f"rss:{feed.name}:offline",
                        title=f"{feed.name} — offline fixture",
                        url=feed.url,
                        snippet=f"Cached placeholder for {category}",
                        content=f"Offline RSS fixture for {feed.name} in {category}.",
                        source_type="rss",
                        tier=2,
                        metadata={"feed": feed.name, "category": category, "offline": True},
                    )
                )
        return docs

    def process_evidence(self, docs: list[SourceDocument]) -> list[dict[str, Any]]:
        claims: list[dict[str, Any]] = []
        for doc in docs:
            try:
                connector = self.source_registry.resolve_parser(doc.source_type or "rss")
            except KeyError:
                from connectors.rss import RssConnector

                connector = RssConnector()
            for claim in connector.extract_evidence(doc):
                stored = self.evidence_store.upsert(claim)
                claims.append(stored)
        return claims

    def update_knowledge_graph(self, topic: str, docs: list[SourceDocument]) -> None:
        topic_node = self.knowledge_graph.upsert_node(NodeType.TOPIC, topic)
        for doc in docs[:40]:
            label = doc.title or doc.url or doc.id
            source_node = self.knowledge_graph.upsert_node(
                NodeType.CONCEPT,
                label[:120],
                source_type=doc.source_type,
                url=doc.url,
            )
            self.knowledge_graph.add_edge(
                topic_node.id,
                source_node.id,
                RelationType.SUPPORTS,
                confidence=doc.confidence,
            )
            try:
                connector = self.source_registry.resolve_parser(doc.source_type or "rss")
            except KeyError:
                continue
            for entity in connector.extract_entities(doc)[:8]:
                ent = self.knowledge_graph.upsert_node(NodeType.CONCEPT, entity)
                self.knowledge_graph.add_edge(source_node.id, ent.id, RelationType.DEPENDS_ON)

    async def run_once(self, *, include_rss: bool = True) -> dict[str, Any]:
        started = datetime.now(timezone.utc).isoformat()
        all_docs: list[SourceDocument] = []
        all_claims: list[dict[str, Any]] = []
        for topic in self.topics:
            docs = await self.collect_from_sources(topic)
            all_docs.extend(docs)
            claims = self.process_evidence(docs)
            all_claims.extend(claims)
            self.update_knowledge_graph(topic, docs)
            self.storage.write_knowledge(
                f"brief_{topic}",
                {
                    "topic": topic,
                    "generated_at": started,
                    "document_count": len(docs),
                    "claim_count": len(claims),
                    "sources": sorted({d.source_type for d in docs}),
                },
            )

        rss_docs: list[SourceDocument] = []
        if include_rss:
            for category in self.rss_registry.categories():
                batch = await self.collect_rss_category(category, limit_per_feed=2)
                rss_docs.extend(batch)
            if rss_docs:
                all_claims.extend(self.process_evidence(rss_docs))
                self.update_knowledge_graph("rss-intelligence", rss_docs)
                all_docs.extend(rss_docs)

        cleanup = self.storage.automatic_cleanup(raw_max_age_hours=self.raw_max_age_hours)
        result = {
            "started_at": started,
            "finished_at": datetime.now(timezone.utc).isoformat(),
            "topics": list(self.topics),
            "sources": self.selected_sources(),
            "documents": len(all_docs),
            "claims": len(all_claims),
            "cleanup": cleanup,
            "knowledge_nodes": len(self.knowledge_graph.nodes()),
            "knowledge_edges": len(self.knowledge_graph.edges()),
        }
        self.last_run = result
        self.storage.write_knowledge("scheduler_last_run", result)
        return result

    def run_once_sync(self, **kwargs: Any) -> dict[str, Any]:
        return asyncio.run(self.run_once(**kwargs))

    def start(self, *, daemon: bool = True) -> None:
        """Start background loop that runs acquisition automatically."""
        if self._thread and self._thread.is_alive():
            return
        self._stop.clear()

        def _loop() -> None:
            while not self._stop.is_set():
                try:
                    self.run_once_sync()
                except Exception:  # noqa: BLE001
                    pass
                self._stop.wait(self.interval_seconds)

        self._thread = threading.Thread(target=_loop, name="intelligence-scheduler", daemon=daemon)
        self._thread.start()

    def stop(self, *, timeout: float = 2.0) -> None:
        self._stop.set()
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=timeout)
