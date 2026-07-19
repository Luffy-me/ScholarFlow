"""Offline-capable producthunt connector."""

from __future__ import annotations

from connectors.base import OfflineFixtureConnector, SourceDocument


class ProducthuntConnector(OfflineFixtureConnector):
    """producthunt connector — works offline; network adapters can replace collect() later."""

    def __init__(self) -> None:
        super().__init__("producthunt", tier=2)


async def collect(query: str, *, limit: int = 5) -> list[SourceDocument]:
    return await ProducthuntConnector().collect(query, limit=limit)
