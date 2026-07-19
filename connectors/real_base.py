"""HTTP-backed connector with automatic offline fixture fallback."""

from __future__ import annotations

from typing import Any, Callable, Awaitable

from connectors.base import OfflineFixtureConnector, SourceDocument


CollectFn = Callable[[str, int], Awaitable[list[SourceDocument]]]


class RealConnector(OfflineFixtureConnector):
    """Try live acquisition; fall back to offline fixtures on any failure."""

    def __init__(
        self,
        name: str,
        tier: int = 2,
        *,
        live_collect: CollectFn | None = None,
    ) -> None:
        super().__init__(name, tier=tier)
        self._live_collect = live_collect

    async def collect(self, query: str, *, limit: int = 5) -> list[SourceDocument]:
        if self._live_collect is not None:
            try:
                docs = await self._live_collect(query, limit)
                if docs:
                    for doc in docs:
                        doc.source_type = doc.source_type or self.name
                        doc.tier = doc.tier or self.tier
                        doc.confidence = self.calculate_confidence(doc)
                        doc.metadata = {
                            **(doc.metadata or {}),
                            "offline": False,
                            "connector": self.name,
                        }
                    return self.deduplicate(docs)[:limit]
            except Exception:  # noqa: BLE001
                pass
        docs = await super().collect(query, limit=limit)
        for doc in docs:
            doc.metadata = {**(doc.metadata or {}), "offline": True, "fallback": True}
        return docs


def docs_from_rss_items(
    items: list[dict[str, str]],
    *,
    connector: str,
    tier: int,
    query: str,
) -> list[SourceDocument]:
    docs: list[SourceDocument] = []
    q = (query or "").lower()
    for i, item in enumerate(items):
        title = item.get("title") or ""
        # Soft relevance filter when query provided
        blob = f"{title} {item.get('snippet', '')}".lower()
        if q and q not in blob and not any(tok in blob for tok in q.split() if len(tok) > 3):
            # still keep some items for discovery feeds
            if i > 2:
                continue
        docs.append(
            SourceDocument(
                id=f"{connector}:{item.get('url') or i}",
                title=title,
                url=item.get("url") or "",
                snippet=item.get("snippet") or "",
                content=item.get("content") or item.get("snippet") or "",
                author=item.get("author") or "",
                published_at=item.get("published_at") or "",
                source_type=connector,
                tier=tier,
                metadata={"query": query},
            )
        )
    return docs
