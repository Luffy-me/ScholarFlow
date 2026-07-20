"""Crossref works API."""

from __future__ import annotations

from connectors.base import SourceDocument
from connectors.http_utils import fetch_json
from connectors.real_base import RealConnector


async def _live(query: str, limit: int) -> list[SourceDocument]:
    data = await fetch_json(
        "https://api.crossref.org/works",
        params={"query": query or "machine learning", "rows": min(max(limit, 5), 20)},
    )
    if not isinstance(data, dict):
        return []
    items = ((data.get("message") or {}).get("items")) or []
    docs: list[SourceDocument] = []
    for row in items:
        title_list = row.get("title") or []
        title = str(title_list[0] if title_list else "").strip()
        if not title:
            continue
        abstract = str(row.get("abstract") or "")
        doi = str(row.get("DOI") or "")
        url = str(row.get("URL") or (f"https://doi.org/{doi}" if doi else ""))
        docs.append(
            SourceDocument(
                id=f"crossref:{doi or title}",
                title=title,
                url=url,
                snippet=abstract[:400] or title,
                content=abstract[:4000] or title,
                source_type="crossref",
                tier=1,
                metadata={"doi": doi, "type": row.get("type")},
            )
        )
        if len(docs) >= limit:
            break
    return docs


class CrossrefConnector(RealConnector):
    def __init__(self) -> None:
        super().__init__("crossref", tier=1, live_collect=_live)
