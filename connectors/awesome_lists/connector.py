"""Offline-capable awesome_lists connector."""

from __future__ import annotations

from connectors.base import OfflineFixtureConnector, SourceDocument


class AwesomeListsConnector(OfflineFixtureConnector):
    """awesome_lists connector — works offline; network adapters can replace collect() later."""

    def __init__(self) -> None:
        super().__init__("awesome_lists", tier=1)


async def collect(query: str, *, limit: int = 5) -> list[SourceDocument]:
    return await AwesomeListsConnector().collect(query, limit=limit)
