"""RSS connector — collect from query URL or default AI feed."""

from __future__ import annotations

from connectors.base import SourceDocument
from connectors.http_utils import fetch_text, parse_rss_items
from connectors.real_base import RealConnector, docs_from_rss_items

DEFAULT_FEED = "https://hnrss.org/frontpage"


async def _live(query: str, limit: int) -> list[SourceDocument]:
    feed = query.strip() if query.startswith("http") else DEFAULT_FEED
    xml = await fetch_text(feed)
    if not xml:
        return []
    items = parse_rss_items(xml, limit=max(limit, 10))
    q = "" if query.startswith("http") else query
    return docs_from_rss_items(items, connector="rss", tier=2, query=q)[:limit]


class RssConnector(RealConnector):
    def __init__(self) -> None:
        super().__init__("rss", tier=2, live_collect=_live)
