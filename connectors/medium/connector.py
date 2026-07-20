"""Medium — RSS only (tag/topic feeds)."""

from __future__ import annotations

from urllib.parse import quote

from connectors.base import SourceDocument
from connectors.http_utils import fetch_text, parse_rss_items
from connectors.real_base import RealConnector, docs_from_rss_items


def _feed_url(query: str) -> str:
    tag = quote((query or "artificial-intelligence").strip().lower().replace(" ", "-")[:64])
    return f"https://medium.com/feed/tag/{tag}"


async def _live(query: str, limit: int) -> list[SourceDocument]:
    xml = await fetch_text(_feed_url(query))
    if not xml:
        # Broad AI tag fallback
        xml = await fetch_text("https://medium.com/feed/tag/artificial-intelligence")
    if not xml:
        return []
    items = parse_rss_items(xml, limit=max(limit, 10))
    return docs_from_rss_items(items, connector="medium", tier=2, query=query)[:limit]


class MediumConnector(RealConnector):
    def __init__(self) -> None:
        super().__init__("medium", tier=2, live_collect=_live)
