"""Offline-capable hackernews connector."""

from __future__ import annotations

from connectors.base import OfflineFixtureConnector, SourceDocument


class HackernewsConnector(OfflineFixtureConnector):
    """hackernews connector — works offline; network adapters can replace collect() later."""

    def __init__(self) -> None:
        super().__init__("hackernews", tier=2)


async def collect(query: str, *, limit: int = 5) -> list[SourceDocument]:
    return await HackernewsConnector().collect(query, limit=limit)
