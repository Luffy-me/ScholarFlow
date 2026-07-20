"""Semantic Scholar academic search."""

from __future__ import annotations

from connectors.base import SourceDocument
from connectors.http_utils import fetch_json
from connectors.real_base import RealConnector


async def _live(query: str, limit: int) -> list[SourceDocument]:
    data = await fetch_json(
        "https://api.semanticscholar.org/graph/v1/paper/search",
        params={
            "query": query or "large language models",
            "limit": min(max(limit, 5), 20),
            "fields": "title,abstract,url,year,citationCount,authors",
        },
    )
    if not isinstance(data, dict):
        return []
    docs: list[SourceDocument] = []
    for row in data.get("data") or []:
        title = str(row.get("title") or "").strip()
        if not title:
            continue
        abstract = str(row.get("abstract") or "")
        paper_id = row.get("paperId") or title
        url = str(row.get("url") or f"https://www.semanticscholar.org/paper/{paper_id}")
        authors = [a.get("name") for a in (row.get("authors") or []) if isinstance(a, dict) and a.get("name")]
        docs.append(
            SourceDocument(
                id=f"semanticscholar:{paper_id}",
                title=title,
                url=url,
                snippet=abstract[:400],
                content=abstract[:4000],
                author=", ".join(authors[:5]),
                published_at=str(row.get("year") or ""),
                source_type="semanticscholar",
                tier=1,
                metadata={"citationCount": row.get("citationCount"), "paperId": paper_id},
            )
        )
        if len(docs) >= limit:
            break
    return docs


class SemanticscholarConnector(RealConnector):
    def __init__(self) -> None:
        super().__init__("semanticscholar", tier=1, live_collect=_live)
