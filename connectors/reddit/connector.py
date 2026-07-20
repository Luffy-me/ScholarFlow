"""Reddit connector — public JSON (.json) endpoints."""

from __future__ import annotations

from urllib.parse import quote_plus

from connectors.base import SourceDocument
from connectors.http_utils import fetch_json
from connectors.real_base import RealConnector


async def _live(query: str, limit: int) -> list[SourceDocument]:
    q = quote_plus(query or "machine learning")
    data = await fetch_json(f"https://www.reddit.com/search.json?q={q}&sort=new&limit={max(limit, 8)}")
    if not isinstance(data, dict):
        return []
    children = (((data.get("data") or {}).get("children")) or [])
    docs: list[SourceDocument] = []
    for child in children:
        post = (child or {}).get("data") or {}
        title = str(post.get("title") or "")
        permalink = str(post.get("permalink") or "")
        url = str(post.get("url") or "")
        if permalink and not url.startswith("http"):
            url = f"https://www.reddit.com{permalink}"
        docs.append(
            SourceDocument(
                id=f"reddit:{post.get('id') or len(docs)}",
                title=title or url,
                url=url,
                snippet=str(post.get("selftext") or "")[:400],
                content=str(post.get("selftext") or title),
                author=str(post.get("author") or ""),
                published_at=str(post.get("created_utc") or ""),
                source_type="reddit",
                tier=2,
                metadata={"subreddit": post.get("subreddit"), "score": post.get("score")},
            )
        )
        if len(docs) >= limit:
            break
    return docs


class RedditConnector(RealConnector):
    def __init__(self) -> None:
        super().__init__("reddit", tier=2, live_collect=_live)
