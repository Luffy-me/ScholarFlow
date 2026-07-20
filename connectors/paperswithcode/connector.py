"""Papers With Code — latest papers API with offline fallback."""

from __future__ import annotations

from urllib.parse import quote_plus

from connectors.base import SourceDocument
from connectors.http_utils import fetch_json, fetch_text, parse_rss_items
from connectors.real_base import RealConnector, docs_from_rss_items


async def _live(query: str, limit: int) -> list[SourceDocument]:
    data = await fetch_json(
        "https://paperswithcode.com/api/v1/papers/",
        params={"q": query or "machine learning", "items_per_page": min(max(limit, 5), 20)},
    )
    docs: list[SourceDocument] = []
    if isinstance(data, dict):
        for row in data.get("results") or []:
            title = str(row.get("title") or "").strip()
            if not title:
                continue
            abstract = str(row.get("abstract") or "")
            url = str(row.get("url_abs") or row.get("url_pdf") or "")
            if not url and row.get("id"):
                url = f"https://paperswithcode.com/paper/{row.get('id')}"
            docs.append(
                SourceDocument(
                    id=f"paperswithcode:{row.get('id') or title}",
                    title=title,
                    url=url,
                    snippet=abstract[:400],
                    content=abstract[:4000],
                    source_type="paperswithcode",
                    tier=1,
                    published_at=str(row.get("published") or "")[:32],
                    metadata={"has_code": True, "pwc_id": row.get("id")},
                )
            )
            if len(docs) >= limit:
                return docs
    # Atom fallback via arXiv
    q = quote_plus(query or "machine learning")
    xml = await fetch_text(
        f"http://export.arxiv.org/api/query?search_query=all:{q}&start=0&max_results={max(limit, 5)}"
    )
    if not xml:
        return docs
    items = parse_rss_items(xml, limit=max(limit, 8))
    fallback = docs_from_rss_items(items, connector="paperswithcode", tier=1, query=query)
    for d in fallback:
        d.metadata = {**(d.metadata or {}), "has_code": False, "via": "arxiv"}
    return (docs + fallback)[:limit]


class PaperswithcodeConnector(RealConnector):
    def __init__(self) -> None:
        super().__init__("paperswithcode", tier=1, live_collect=_live)
