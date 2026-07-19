"""Offline-capable google_news connector."""

from __future__ import annotations

from connectors.base import OfflineFixtureConnector, SourceDocument


class GoogleNewsConnector(OfflineFixtureConnector):
    """google_news connector — works offline; network adapters can replace collect() later."""

    def __init__(self) -> None:
        super().__init__("google_news", tier=2)


async def collect(query: str, *, limit: int = 5) -> list[SourceDocument]:
    return await GoogleNewsConnector().collect(query, limit=limit)
