"""Offline-capable rss connector."""

from __future__ import annotations

from connectors.base import OfflineFixtureConnector, SourceDocument


class RssConnector(OfflineFixtureConnector):
    """rss connector — works offline; network adapters can replace collect() later."""

    def __init__(self) -> None:
        super().__init__("rss", tier=2)


async def collect(query: str, *, limit: int = 5) -> list[SourceDocument]:
    return await RssConnector().collect(query, limit=limit)
