"""Offline-capable github connector."""

from __future__ import annotations

from connectors.base import OfflineFixtureConnector, SourceDocument


class GithubConnector(OfflineFixtureConnector):
    """github connector — works offline; network adapters can replace collect() later."""

    def __init__(self) -> None:
        super().__init__("github", tier=1)


async def collect(query: str, *, limit: int = 5) -> list[SourceDocument]:
    return await GithubConnector().collect(query, limit=limit)
