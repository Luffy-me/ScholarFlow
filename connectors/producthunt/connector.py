"""Product Hunt — public RSS feed (no API key)."""

from __future__ import annotations

from connectors.base import SourceDocument
from connectors.http_utils import fetch_text, parse_rss_items
from connectors.real_base import RealConnector, docs_from_rss_items

FEED_URL = "https://www.producthunt.com/feed"


async def _live(query: str, limit: int) -> list[SourceDocument]:
    xml = await fetch_text(FEED_URL)
    if not xml:
        return []
    items = parse_rss_items(xml, limit=max(limit, 12))
    return docs_from_rss_items(items, connector="producthunt", tier=2, query=query)[:limit]


class ProducthuntConnector(RealConnector):
    def __init__(self) -> None:
        super().__init__("producthunt", tier=2, live_collect=_live)
