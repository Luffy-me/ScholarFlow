"""OpenAlex works API."""

from __future__ import annotations

from connectors.base import SourceDocument
from connectors.http_utils import fetch_json
from connectors.real_base import RealConnector


def _reconstruct_abstract(inv: dict) -> str:
    positions: list[tuple[int, str]] = []
    for word, idxs in inv.items():
        if not isinstance(idxs, list):
            continue
        for i in idxs:
            try:
                positions.append((int(i), str(word)))
            except (TypeError, ValueError):
                continue
    return " ".join(w for _, w in sorted(positions))[:4000]


async def _live(query: str, limit: int) -> list[SourceDocument]:
    data = await fetch_json(
        "https://api.openalex.org/works",
        params={
            "search": query or "artificial intelligence",
            "per-page": min(max(limit, 5), 25),
            "mailto": "linkedai-local@example.com",
        },
    )
    if not isinstance(data, dict):
        return []
    docs: list[SourceDocument] = []
    for row in data.get("results") or []:
        title = str(row.get("title") or "").strip()
        if not title:
            continue
        abstract = ""
        inv = row.get("abstract_inverted_index")
        if isinstance(inv, dict):
            abstract = _reconstruct_abstract(inv)
        loc = row.get("primary_location") or {}
        url = str(loc.get("landing_page_url") or row.get("id") or "")
        docs.append(
            SourceDocument(
                id=f"openalex:{row.get('id') or title}",
                title=title,
                url=url,
                snippet=abstract[:400] or title,
                content=abstract or title,
                published_at=str(row.get("publication_date") or row.get("publication_year") or "")[:32],
                source_type="openalex",
                tier=1,
                metadata={"cited_by_count": row.get("cited_by_count"), "openalex_id": row.get("id")},
            )
        )
        if len(docs) >= limit:
            break
    return docs


class OpenalexConnector(RealConnector):
    def __init__(self) -> None:
        super().__init__("openalex", tier=1, live_collect=_live)
