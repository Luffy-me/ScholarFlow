"""Hugging Face Daily Papers."""

from __future__ import annotations

from connectors.base import SourceDocument
from connectors.http_utils import fetch_json
from connectors.real_base import RealConnector


async def _live(query: str, limit: int) -> list[SourceDocument]:
    data = await fetch_json("https://huggingface.co/api/daily_papers")
    if not isinstance(data, list):
        return []
    q = (query or "").lower()
    docs: list[SourceDocument] = []
    for row in data:
        paper = row.get("paper") if isinstance(row.get("paper"), dict) else row
        if not isinstance(paper, dict):
            continue
        title = str(paper.get("title") or "").strip()
        if not title:
            continue
        blob = f"{title} {paper.get('summary') or ''}".lower()
        if q and q not in blob and not any(t in blob for t in q.split() if len(t) > 3):
            if len(docs) >= 2:
                continue
        paper_id = str(paper.get("id") or title)
        url = f"https://huggingface.co/papers/{paper_id}" if paper.get("id") else ""
        summary = str(paper.get("summary") or "")
        docs.append(
            SourceDocument(
                id=f"huggingface_papers:{paper_id}",
                title=title,
                url=url,
                snippet=summary[:400],
                content=summary[:4000],
                published_at=str(row.get("publishedAt") or paper.get("publishedAt") or "")[:32],
                source_type="huggingface_papers",
                tier=1,
                metadata={"upvotes": row.get("upvotes") or paper.get("upvotes")},
            )
        )
        if len(docs) >= limit:
            break
    return docs


class HuggingfacePapersConnector(RealConnector):
    def __init__(self) -> None:
        super().__init__("huggingface_papers", tier=1, live_collect=_live)
