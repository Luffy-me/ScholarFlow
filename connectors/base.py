"""Provider-agnostic research connector interface.

External APIs are optional. Offline/local fixtures must always work.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any


SOURCE_TIERS: dict[str, int] = {
    # Tier 1
    "official_docs": 1,
    "arxiv": 1,
    "paperswithcode": 1,
    "github": 1,
    "huggingface": 1,
    "awesome_lists": 1,
    # Tier 2
    "hackernews": 2,
    "lobsters": 2,
    "reddit": 2,
    "devto": 2,
    "medium": 2,
    "producthunt": 2,
    "rss": 2,
    "google_news": 2,
    "stackoverflow": 2,
    # Tier 3
    "youtube": 3,
    # Future
    "linkedin": 2,
    "x": 3,
    "news_api": 2,
}


@dataclass
class SourceDocument:
    id: str
    title: str
    url: str = ""
    snippet: str = ""
    content: str = ""
    source_type: str = ""
    author: str = ""
    published_at: str = ""
    tier: int = 2
    confidence: float = 0.5
    metadata: dict[str, Any] = field(default_factory=dict)

    def normalize(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "title": self.title.strip(),
            "url": self.url.strip(),
            "snippet": (self.snippet or self.content[:280]).strip(),
            "content": self.content.strip(),
            "source_type": self.source_type,
            "author": self.author,
            "published_at": self.published_at or datetime.now(timezone.utc).isoformat(),
            "tier": self.tier,
            "confidence": max(0.0, min(1.0, float(self.confidence))),
            "metadata": self.metadata,
        }


class BaseConnector(ABC):
    """Every connector implements collect/search/summarize/extract/normalize/confidence."""

    name: str = "base"
    tier: int = 2
    offline_capable: bool = True

    @abstractmethod
    async def collect(self, query: str, *, limit: int = 5) -> list[SourceDocument]:
        raise NotImplementedError

    async def search(self, query: str, *, limit: int = 5) -> list[SourceDocument]:
        return await self.collect(query, limit=limit)

    async def summarize(self, documents: list[SourceDocument]) -> str:
        if not documents:
            return ""
        titles = [d.title for d in documents[:5] if d.title]
        return f"{self.name} summary for {len(documents)} docs: " + "; ".join(titles)

    async def extract(self, document: SourceDocument) -> list[str]:
        text = document.content or document.snippet or document.title
        parts = [p.strip() for p in text.replace("!", ".").split(".") if len(p.strip()) > 20]
        return parts[:5]

    def normalize(self, document: SourceDocument) -> dict[str, Any]:
        payload = document.normalize()
        payload["source_type"] = payload.get("source_type") or self.name
        payload["tier"] = SOURCE_TIERS.get(self.name, self.tier)
        return payload

    def confidence(self, document: SourceDocument) -> float:
        base = 0.85 if self.tier == 1 else 0.65 if self.tier == 2 else 0.45
        if document.url:
            base += 0.05
        if document.content and len(document.content) > 120:
            base += 0.05
        return max(0.0, min(1.0, base))


class OfflineFixtureConnector(BaseConnector):
    """Local-first connector that synthesizes documents without network calls."""

    def __init__(self, name: str, tier: int = 2, *, seed_topics: list[str] | None = None) -> None:
        self.name = name
        self.tier = tier
        self.seed_topics = seed_topics or []

    async def collect(self, query: str, *, limit: int = 5) -> list[SourceDocument]:
        q = (query or "topic").strip()
        docs: list[SourceDocument] = []
        for i in range(max(1, min(limit, 3))):
            doc = SourceDocument(
                id=f"{self.name}:{q.lower().replace(' ', '-')}:{i}",
                title=f"{q} — {self.name} perspective #{i + 1}",
                url=f"local://{self.name}/{i}",
                snippet=f"Offline {self.name} signal about {q}: practitioners discuss tradeoffs and constraints.",
                content=(
                    f"Local fixture from {self.name} on {q}. "
                    f"Recurring theme: evaluation quality and workflow design matter more than slogans. "
                    f"Pain point: generic advice ignores operational constraints."
                ),
                source_type=self.name,
                tier=self.tier,
                confidence=0.55 if self.tier > 1 else 0.8,
                metadata={"offline": True, "connector": self.name},
            )
            doc.confidence = self.confidence(doc)
            docs.append(doc)
        return docs
