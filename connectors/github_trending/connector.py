"""GitHub Trending connector — public trending scrape endpoint fallback via gh API search."""

from __future__ import annotations

from urllib.parse import quote_plus

from connectors.base import SourceDocument
from connectors.http_utils import fetch_json
from connectors.real_base import RealConnector


async def _live(query: str, limit: int) -> list[SourceDocument]:
    q = quote_plus((query or "artificial intelligence") + " in:name,description stars:>50")
    data = await fetch_json(
        f"https://api.github.com/search/repositories?q={q}&sort=stars&order=desc&per_page={max(limit, 5)}"
    )
    if not isinstance(data, dict):
        return []
    docs: list[SourceDocument] = []
    for repo in data.get("items") or []:
        docs.append(
            SourceDocument(
                id=f"github_trending:{repo.get('full_name')}",
                title=str(repo.get("full_name") or repo.get("name") or ""),
                url=str(repo.get("html_url") or ""),
                snippet=str(repo.get("description") or "")[:400],
                content=str(repo.get("description") or ""),
                author=str(((repo.get("owner") or {}).get("login")) or ""),
                published_at=str(repo.get("updated_at") or repo.get("created_at") or ""),
                source_type="github_trending",
                tier=1,
                metadata={
                    "stars": repo.get("stargazers_count"),
                    "language": repo.get("language"),
                    "forks": repo.get("forks_count"),
                },
            )
        )
        if len(docs) >= limit:
            break
    return docs


class GithubTrendingConnector(RealConnector):
    def __init__(self) -> None:
        super().__init__("github_trending", tier=1, live_collect=_live)
