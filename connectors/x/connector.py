"""Offline-capable x connector."""

from __future__ import annotations

from connectors.base import OfflineFixtureConnector, SourceDocument


class XConnector(OfflineFixtureConnector):
    """x connector — works offline; network adapters can replace collect() later."""

    def __init__(self) -> None:
        super().__init__("x", tier=3)


async def collect(query: str, *, limit: int = 5) -> list[SourceDocument]:
    return await XConnector().collect(query, limit=limit)
