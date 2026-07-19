"""Offline-capable stackoverflow connector."""

from __future__ import annotations

from connectors.base import OfflineFixtureConnector, SourceDocument


class StackoverflowConnector(OfflineFixtureConnector):
    """stackoverflow connector — works offline; network adapters can replace collect() later."""

    def __init__(self) -> None:
        super().__init__("stackoverflow", tier=2)


async def collect(query: str, *, limit: int = 5) -> list[SourceDocument]:
    return await StackoverflowConnector().collect(query, limit=limit)
