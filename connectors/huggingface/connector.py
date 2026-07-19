"""Hugging Face — models hub (compat alias)."""

from __future__ import annotations

from connectors.base import SourceDocument
from connectors.huggingface_models import connector as models
from connectors.real_base import RealConnector


async def _live(query: str, limit: int) -> list[SourceDocument]:
    docs = await models._live(query, limit)
    for doc in docs:
        doc.source_type = "huggingface"
        if doc.id.startswith("huggingface_models:"):
            doc.id = "huggingface:" + doc.id.split(":", 1)[1]
    return docs


class HuggingfaceConnector(RealConnector):
    def __init__(self) -> None:
        super().__init__("huggingface", tier=1, live_collect=_live)
