"""Connector registry — add sources without changing agent code."""

from __future__ import annotations

from typing import Callable

from connectors.arxiv import ArxivConnector
from connectors.awesome_lists import AwesomeListsConnector
from connectors.base import BaseConnector
from connectors.devto import DevtoConnector
from connectors.github import GithubConnector
from connectors.google_news import GoogleNewsConnector
from connectors.hackernews import HackernewsConnector
from connectors.huggingface import HuggingfaceConnector
from connectors.linkedin import LinkedinConnector
from connectors.lobsters import LobstersConnector
from connectors.medium import MediumConnector
from connectors.news_api import NewsApiConnector
from connectors.official_docs import OfficialDocsConnector
from connectors.paperswithcode import PaperswithcodeConnector
from connectors.producthunt import ProducthuntConnector
from connectors.reddit import RedditConnector
from connectors.rss import RssConnector
from connectors.stackoverflow import StackoverflowConnector
from connectors.x import XConnector
from connectors.youtube import YoutubeConnector

_FACTORY: dict[str, Callable[[], BaseConnector]] = {
    "rss": RssConnector,
    "reddit": RedditConnector,
    "github": GithubConnector,
    "arxiv": ArxivConnector,
    "hackernews": HackernewsConnector,
    "lobsters": LobstersConnector,
    "devto": DevtoConnector,
    "medium": MediumConnector,
    "stackoverflow": StackoverflowConnector,
    "youtube": YoutubeConnector,
    "google_news": GoogleNewsConnector,
    "producthunt": ProducthuntConnector,
    "huggingface": HuggingfaceConnector,
    "paperswithcode": PaperswithcodeConnector,
    "awesome_lists": AwesomeListsConnector,
    "official_docs": OfficialDocsConnector,
    "linkedin": LinkedinConnector,
    "x": XConnector,
    "news_api": NewsApiConnector,
}


def list_connectors() -> list[str]:
    return sorted(_FACTORY)


def get_connector(name: str) -> BaseConnector:
    key = (name or "").strip().lower()
    if key not in _FACTORY:
        raise KeyError(f"Unknown connector: {name}. Available: {list_connectors()}")
    return _FACTORY[key]()


def register_connector(name: str, factory: Callable[[], BaseConnector]) -> None:
    """Hot-register future connectors (Firecrawl, Tavily, etc.) without agent changes."""
    _FACTORY[name.strip().lower()] = factory
