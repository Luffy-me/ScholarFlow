"""GitHub connector — delegates to trending search (compat name)."""

from __future__ import annotations

from connectors.github_trending.connector import GithubTrendingConnector, _live
from connectors.real_base import RealConnector


class GithubConnector(RealConnector):
    def __init__(self) -> None:
        super().__init__("github", tier=1, live_collect=_live)
