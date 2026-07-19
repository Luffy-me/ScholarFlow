"""Hacker News connector — Firebase API."""

from __future__ import annotations

from connectors.base import SourceDocument
from connectors.http_utils import fetch_json
from connectors.real_base import RealConnector


async def _live(query: str, limit: int) -> list[SourceDocument]:
    ids = await fetch_json("https://hacker-news.firebaseio.com/v0/topstories.json")
    if not isinstance(ids, list):
        return []
    docs: list[SourceDocument] = []
    q = (query or "").lower()
    for story_id in ids[:40]:
        item = await fetch_json(f"https://hacker-news.firebaseio.com/v0/item/{story_id}.json")
        if not isinstance(item, dict):
            continue
        title = str(item.get("title") or "")
        if q and q not in title.lower() and not any(t in title.lower() for t in q.split() if len(t) > 3):
            if len(docs) >= 2:
                continue
        url = str(item.get("url") or f"https://news.ycombinator.com/item?id={story_id}")
        docs.append(
            SourceDocument(
                id=f"hackernews:{story_id}",
                title=title or url,
                url=url,
                snippet=f"score={item.get('score', 0)} comments={item.get('descendants', 0)}",
                content=title,
                author=str(item.get("by") or ""),
                published_at=str(item.get("time") or ""),
                source_type="hackernews",
                tier=2,
                metadata={"score": item.get("score"), "hn_id": story_id},
            )
        )
        if len(docs) >= limit:
            break
    return docs


class HackernewsConnector(RealConnector):
    def __init__(self) -> None:
        super().__init__("hackernews", tier=2, live_collect=_live)
