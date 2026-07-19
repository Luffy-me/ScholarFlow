"""Offline-capable lobsters connector."""

from __future__ import annotations

from connectors.base import OfflineFixtureConnector, SourceDocument


class LobstersConnector(OfflineFixtureConnector):
    """lobsters connector — works offline; network adapters can replace collect() later."""

    def __init__(self) -> None:
        super().__init__("lobsters", tier=2)


async def collect(query: str, *, limit: int = 5) -> list[SourceDocument]:
    return await LobstersConnector().collect(query, limit=limit)
