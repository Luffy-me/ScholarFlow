"""arXiv connector — Atom API."""

from __future__ import annotations

from urllib.parse import quote_plus

from connectors.base import SourceDocument
from connectors.http_utils import fetch_text, parse_rss_items
from connectors.real_base import RealConnector, docs_from_rss_items


async def _live(query: str, limit: int) -> list[SourceDocument]:
    q = quote_plus(query or "machine learning")
    url = f"http://export.arxiv.org/api/query?search_query=all:{q}&start=0&max_results={max(limit, 5)}"
    xml = await fetch_text(url)
    if not xml:
        return []
    items = parse_rss_items(xml, limit=max(limit, 8))
    return docs_from_rss_items(items, connector="arxiv", tier=1, query=query)[:limit]


class ArxivConnector(RealConnector):
    def __init__(self) -> None:
        super().__init__("arxiv", tier=1, live_collect=_live)
