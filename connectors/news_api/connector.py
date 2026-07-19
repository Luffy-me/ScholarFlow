"""Offline-capable news_api connector."""

from __future__ import annotations

from connectors.base import OfflineFixtureConnector, SourceDocument


class NewsApiConnector(OfflineFixtureConnector):
    """news_api connector — works offline; network adapters can replace collect() later."""

    def __init__(self) -> None:
        super().__init__("news_api", tier=2)


async def collect(query: str, *, limit: int = 5) -> list[SourceDocument]:
    return await NewsApiConnector().collect(query, limit=limit)
