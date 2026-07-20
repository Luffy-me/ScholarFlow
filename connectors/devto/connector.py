"""Dev.to public articles API."""

from __future__ import annotations

from connectors.base import SourceDocument
from connectors.http_utils import fetch_json
from connectors.real_base import RealConnector


async def _live(query: str, limit: int) -> list[SourceDocument]:
    tag = (query or "ai").strip().lower().split()[0][:32]
    data = await fetch_json(
        "https://dev.to/api/articles",
        params={"tag": tag, "per_page": min(max(limit, 5), 20), "top": "7"},
    )
    if not isinstance(data, list):
        data = await fetch_json(
            "https://dev.to/api/articles",
            params={"per_page": min(max(limit, 5), 20)},
        )
    if not isinstance(data, list):
        return []
    docs: list[SourceDocument] = []
    q = (query or "").lower()
    for row in data:
        title = str(row.get("title") or "").strip()
        if not title:
            continue
        desc = str(row.get("description") or "")
        blob = f"{title} {desc}".lower()
        if q and q not in blob and not any(t in blob for t in q.split() if len(t) > 3):
            if len(docs) >= 2:
                continue
        url = str(row.get("url") or "")
        docs.append(
            SourceDocument(
                id=f"devto:{row.get('id') or title}",
                title=title,
                url=url,
                snippet=desc[:400],
                content=desc,
                author=str(((row.get("user") or {}).get("username")) or ""),
                published_at=str(row.get("published_at") or "")[:32],
                source_type="devto",
                tier=2,
                metadata={"positive_reactions_count": row.get("positive_reactions_count"), "tags": row.get("tag_list")},
            )
        )
        if len(docs) >= limit:
            break
    return docs


class DevtoConnector(RealConnector):
    def __init__(self) -> None:
        super().__init__("devto", tier=2, live_collect=_live)
