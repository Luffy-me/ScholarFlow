"""Offline-capable youtube connector."""

from __future__ import annotations

from connectors.base import OfflineFixtureConnector, SourceDocument


class YoutubeConnector(OfflineFixtureConnector):
    """youtube connector — works offline; network adapters can replace collect() later."""

    def __init__(self) -> None:
        super().__init__("youtube", tier=3)


async def collect(query: str, *, limit: int = 5) -> list[SourceDocument]:
    return await YoutubeConnector().collect(query, limit=limit)
