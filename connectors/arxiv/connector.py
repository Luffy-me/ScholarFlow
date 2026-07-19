"""Offline-capable arxiv connector."""

from __future__ import annotations

from connectors.base import OfflineFixtureConnector, SourceDocument


class ArxivConnector(OfflineFixtureConnector):
    """arxiv connector — works offline; network adapters can replace collect() later."""

    def __init__(self) -> None:
        super().__init__("arxiv", tier=1)


async def collect(query: str, *, limit: int = 5) -> list[SourceDocument]:
    return await ArxivConnector().collect(query, limit=limit)
