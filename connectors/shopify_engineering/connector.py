"""shopify_engineering connector — live RSS/HTTP with offline fallback."""

from __future__ import annotations

from connectors.base import SourceDocument
from connectors.http_utils import fetch_text, parse_rss_items
from connectors.real_base import RealConnector, docs_from_rss_items

FEED_URL = "https://shopify.engineering/feed.xml"
TIER = 2


async def _live(query: str, limit: int) -> list[SourceDocument]:
    xml = await fetch_text(FEED_URL)
    if not xml:
        return []
    items = parse_rss_items(xml, limit=max(limit, 8))
    return docs_from_rss_items(items, connector="shopify_engineering", tier=TIER, query=query)[:limit]


class ShopifyEngineeringConnector(RealConnector):
    def __init__(self) -> None:
        super().__init__("shopify_engineering", tier=TIER, live_collect=_live)


async def collect(query: str, *, limit: int = 5) -> list[SourceDocument]:
    return await ShopifyEngineeringConnector().collect(query, limit=limit)
