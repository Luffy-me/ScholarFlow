"""Offline-capable official_docs connector."""

from __future__ import annotations

from connectors.base import OfflineFixtureConnector, SourceDocument


class OfficialDocsConnector(OfflineFixtureConnector):
    """official_docs connector — works offline; network adapters can replace collect() later."""

    def __init__(self) -> None:
        super().__init__("official_docs", tier=1)


async def collect(query: str, *, limit: int = 5) -> list[SourceDocument]:
    return await OfficialDocsConnector().collect(query, limit=limit)
