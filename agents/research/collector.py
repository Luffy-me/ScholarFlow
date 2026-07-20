"""Collect documents from registered connectors (offline-capable)."""

from __future__ import annotations

from typing import Any

from connectors.base import SourceDocument
from connectors.registry import get_connector, list_connectors
from models.capabilities import Capability


class ResearchCollector:
    name = "research_collector"
    capabilities = [Capability.RESEARCH]

    DEFAULT_CONNECTORS = (
        "official_docs",
        "arxiv",
        "github",
        "hackernews",
        "reddit",
        "devto",
        "huggingface",
        "paperswithcode",
    )

    def __init__(self, connector_names: list[str] | None = None) -> None:
        self.connector_names = connector_names or list(self.DEFAULT_CONNECTORS)

    async def collect(self, query: str, *, limit_per_source: int = 2) -> list[SourceDocument]:
        docs: list[SourceDocument] = []
        for name in self.connector_names:
            if name not in list_connectors():
                continue
            connector = get_connector(name)
            try:
                found = await connector.collect(query, limit=limit_per_source)
            except Exception:  # noqa: BLE001 - offline resilience
                found = []
            docs.extend(found)
        return docs

    def stats(self, documents: list[SourceDocument]) -> dict[str, int]:
        counts: dict[str, int] = {}
        for doc in documents:
            key = doc.source_type or "unknown"
            counts[key] = counts.get(key, 0) + 1
        return counts

    def normalize_all(self, documents: list[SourceDocument]) -> list[dict[str, Any]]:
        out: list[dict[str, Any]] = []
        for doc in documents:
            connector = get_connector(doc.source_type) if doc.source_type in list_connectors() else None
            if connector:
                out.append(connector.normalize(doc))
            else:
                out.append(doc.normalize())
        return out
