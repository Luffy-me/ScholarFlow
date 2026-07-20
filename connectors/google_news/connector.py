"""Google News RSS search."""

from __future__ import annotations

from urllib.parse import quote_plus

from connectors.base import SourceDocument
from connectors.http_utils import fetch_text, parse_rss_items
from connectors.real_base import RealConnector, docs_from_rss_items


async def _live(query: str, limit: int) -> list[SourceDocument]:
    q = quote_plus(query or "artificial intelligence")
    xml = await fetch_text(f"https://news.google.com/rss/search?q={q}&hl=en-US&gl=US&ceid=US:en")
    if not xml:
        return []
    items = parse_rss_items(xml, limit=max(limit, 10))
    return docs_from_rss_items(items, connector="google_news", tier=2, query=query)[:limit]


class GoogleNewsConnector(RealConnector):
    def __init__(self) -> None:
        super().__init__("google_news", tier=2, live_collect=_live)
