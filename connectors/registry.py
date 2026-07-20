"""Connector registry — add sources without changing agent code."""

from __future__ import annotations

from typing import Callable

from connectors.anthropic_blog import AnthropicBlogConnector
from connectors.arxiv import ArxivConnector
from connectors.awesome_lists import AwesomeListsConnector
from connectors.base import BaseConnector
from connectors.cloudflare_blog import CloudflareBlogConnector
from connectors.crossref import CrossrefConnector
from connectors.deepmind_blog import DeepmindBlogConnector
from connectors.devto import DevtoConnector
from connectors.github import GithubConnector
from connectors.github_releases import GithubReleasesConnector
from connectors.github_trending import GithubTrendingConnector
from connectors.google_news import GoogleNewsConnector
from connectors.hackernews import HackernewsConnector
from connectors.hashnode import HashnodeConnector
from connectors.huggingface import HuggingfaceConnector
from connectors.huggingface_models import HuggingfaceModelsConnector
from connectors.huggingface_papers import HuggingfacePapersConnector
from connectors.linear_blog import LinearBlogConnector
from connectors.linkedin import LinkedinConnector
from connectors.lobsters import LobstersConnector
from connectors.medium import MediumConnector
from connectors.netflix_tech_blog import NetflixTechBlogConnector
from connectors.news_api import NewsApiConnector
from connectors.official_docs import OfficialDocsConnector
from connectors.openai_blog import OpenaiBlogConnector
from connectors.openalex import OpenalexConnector
from connectors.paperswithcode import PaperswithcodeConnector
from connectors.producthunt import ProducthuntConnector
from connectors.reddit import RedditConnector
from connectors.rss import RssConnector
from connectors.semanticscholar import SemanticscholarConnector
from connectors.shopify_engineering import ShopifyEngineeringConnector
from connectors.stackoverflow import StackoverflowConnector
from connectors.stackoverflow_blog import StackoverflowBlogConnector
from connectors.stripe_engineering import StripeEngineeringConnector
from connectors.uber_engineering import UberEngineeringConnector
from connectors.vercel_blog import VercelBlogConnector
from connectors.x import XConnector
from connectors.youtube import YoutubeConnector

_FACTORY: dict[str, Callable[[], BaseConnector]] = {
    "rss": RssConnector,
    "reddit": RedditConnector,
    "github": GithubConnector,
    "github_trending": GithubTrendingConnector,
    "github_releases": GithubReleasesConnector,
    "arxiv": ArxivConnector,
    "paperswithcode": PaperswithcodeConnector,
    "semanticscholar": SemanticscholarConnector,
    "semantic_scholar": SemanticscholarConnector,
    "openalex": OpenalexConnector,
    "crossref": CrossrefConnector,
    "hackernews": HackernewsConnector,
    "lobsters": LobstersConnector,
    "devto": DevtoConnector,
    "medium": MediumConnector,
    "hashnode": HashnodeConnector,
    "stackoverflow": StackoverflowConnector,
    "stackoverflow_blog": StackoverflowBlogConnector,
    "youtube": YoutubeConnector,
    "google_news": GoogleNewsConnector,
    "producthunt": ProducthuntConnector,
    "huggingface": HuggingfaceConnector,
    "huggingface_models": HuggingfaceModelsConnector,
    "huggingface_papers": HuggingfacePapersConnector,
    "awesome_lists": AwesomeListsConnector,
    "official_docs": OfficialDocsConnector,
    "openai_blog": OpenaiBlogConnector,
    "anthropic_blog": AnthropicBlogConnector,
    "deepmind_blog": DeepmindBlogConnector,
    "cloudflare_blog": CloudflareBlogConnector,
    "stripe_engineering": StripeEngineeringConnector,
    "vercel_blog": VercelBlogConnector,
    "linear_blog": LinearBlogConnector,
    "netflix_tech_blog": NetflixTechBlogConnector,
    "uber_engineering": UberEngineeringConnector,
    "shopify_engineering": ShopifyEngineeringConnector,
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
