"""GitHub Releases connector — public releases API for popular orgs."""

from __future__ import annotations

from connectors.base import SourceDocument
from connectors.http_utils import fetch_json
from connectors.real_base import RealConnector

DEFAULT_REPOS = (
    "ollama/ollama",
    "huggingface/transformers",
    "openai/openai-python",
    "anthropics/anthropic-sdk-python",
)


async def _live(query: str, limit: int) -> list[SourceDocument]:
    docs: list[SourceDocument] = []
    q = (query or "").lower()
    repos = DEFAULT_REPOS
    if "/" in (query or "") and " " not in query:
        repos = (query.strip(),)
    for repo in repos:
        data = await fetch_json(f"https://api.github.com/repos/{repo}/releases?per_page=5")
        if not isinstance(data, list):
            continue
        for rel in data:
            title = str(rel.get("name") or rel.get("tag_name") or "")
            body = str(rel.get("body") or "")
            if q and "/" not in q and q not in (title + body).lower():
                continue
            docs.append(
                SourceDocument(
                    id=f"github_releases:{repo}:{rel.get('id')}",
                    title=f"{repo} {title}".strip(),
                    url=str(rel.get("html_url") or ""),
                    snippet=body[:400],
                    content=body,
                    author=str(((rel.get("author") or {}).get("login")) or ""),
                    published_at=str(rel.get("published_at") or ""),
                    source_type="github_releases",
                    tier=1,
                    metadata={"repo": repo, "tag": rel.get("tag_name")},
                )
            )
            if len(docs) >= limit:
                return docs
    return docs


class GithubReleasesConnector(RealConnector):
    def __init__(self) -> None:
        super().__init__("github_releases", tier=1, live_collect=_live)
