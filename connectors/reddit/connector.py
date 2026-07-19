"""Offline-capable reddit connector."""

from __future__ import annotations

from connectors.base import OfflineFixtureConnector, SourceDocument


class RedditConnector(OfflineFixtureConnector):
    """reddit connector — works offline; network adapters can replace collect() later."""

    def __init__(self) -> None:
        super().__init__("reddit", tier=2)


async def collect(query: str, *, limit: int = 5) -> list[SourceDocument]:
    return await RedditConnector().collect(query, limit=limit)
