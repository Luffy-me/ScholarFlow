"""Offline-capable devto connector."""

from __future__ import annotations

from connectors.base import OfflineFixtureConnector, SourceDocument


class DevtoConnector(OfflineFixtureConnector):
    """devto connector — works offline; network adapters can replace collect() later."""

    def __init__(self) -> None:
        super().__init__("devto", tier=2)


async def collect(query: str, *, limit: int = 5) -> list[SourceDocument]:
    return await DevtoConnector().collect(query, limit=limit)
