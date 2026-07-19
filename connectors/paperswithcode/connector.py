"""Offline-capable paperswithcode connector."""

from __future__ import annotations

from connectors.base import OfflineFixtureConnector, SourceDocument


class PaperswithcodeConnector(OfflineFixtureConnector):
    """paperswithcode connector — works offline; network adapters can replace collect() later."""

    def __init__(self) -> None:
        super().__init__("paperswithcode", tier=1)


async def collect(query: str, *, limit: int = 5) -> list[SourceDocument]:
    return await PaperswithcodeConnector().collect(query, limit=limit)
