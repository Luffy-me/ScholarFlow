"""Offline-capable linkedin connector."""

from __future__ import annotations

from connectors.base import OfflineFixtureConnector, SourceDocument


class LinkedinConnector(OfflineFixtureConnector):
    """linkedin connector — works offline; network adapters can replace collect() later."""

    def __init__(self) -> None:
        super().__init__("linkedin", tier=2)


async def collect(query: str, *, limit: int = 5) -> list[SourceDocument]:
    return await LinkedinConnector().collect(query, limit=limit)
