"""Offline-capable huggingface connector."""

from __future__ import annotations

from connectors.base import OfflineFixtureConnector, SourceDocument


class HuggingfaceConnector(OfflineFixtureConnector):
    """huggingface connector — works offline; network adapters can replace collect() later."""

    def __init__(self) -> None:
        super().__init__("huggingface", tier=1)


async def collect(query: str, *, limit: int = 5) -> list[SourceDocument]:
    return await HuggingfaceConnector().collect(query, limit=limit)
