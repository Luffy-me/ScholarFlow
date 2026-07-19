"""Offline-capable medium connector."""

from __future__ import annotations

from connectors.base import OfflineFixtureConnector, SourceDocument


class MediumConnector(OfflineFixtureConnector):
    """medium connector — works offline; network adapters can replace collect() later."""

    def __init__(self) -> None:
        super().__init__("medium", tier=2)


async def collect(query: str, *, limit: int = 5) -> list[SourceDocument]:
    return await MediumConnector().collect(query, limit=limit)
