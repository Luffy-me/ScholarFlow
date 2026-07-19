"""Source Registry — authority, freshness, trust, and parser binding."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Callable

from connectors.base import SOURCE_TIERS, BaseConnector
from connectors.registry import get_connector, list_connectors, register_connector


@dataclass(frozen=True)
class SourceSpec:
    name: str
    authority_score: float
    freshness_weight: float
    update_frequency: str
    category: str
    trust_level: str
    parser: str
    tier: int = 2
    enabled: bool = True
    metadata: dict[str, Any] = field(default_factory=dict)

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


def _authority_from_tier(tier: int) -> float:
    return {1: 0.92, 2: 0.72, 3: 0.48}.get(tier, 0.6)


def _trust_from_tier(tier: int) -> str:
    return {1: "high", 2: "medium", 3: "low"}.get(tier, "medium")


def _freshness_for(category: str, name: str) -> float:
    if name in {"hackernews", "lobsters", "reddit", "producthunt", "github_trending"}:
        return 0.95
    if category in {"ai", "ml", "programming", "open_source", "cybersecurity", "cloud"}:
        return 0.8
    if category in {"economics", "finance", "business", "startups"}:
        return 0.7
    return 0.75


def _frequency_for(name: str, category: str) -> str:
    if name in {"hackernews", "lobsters", "reddit", "github_trending", "producthunt"}:
        return "hourly"
    if category in {"ai", "ml", "programming", "open_source", "cybersecurity", "cloud"}:
        return "daily"
    if name.endswith("_blog") or "engineering" in name:
        return "daily"
    if name in {"arxiv", "paperswithcode", "semanticscholar", "openalex", "crossref"}:
        return "daily"
    return "weekly"


_CATEGORY_BY_SOURCE: dict[str, str] = {
    "arxiv": "ai",
    "paperswithcode": "ml",
    "semanticscholar": "ai",
    "semantic_scholar": "ai",
    "openalex": "ai",
    "crossref": "ai",
    "huggingface": "ai",
    "huggingface_models": "ai",
    "huggingface_papers": "ml",
    "openai_blog": "ai",
    "anthropic_blog": "ai",
    "deepmind_blog": "ai",
    "github": "open_source",
    "github_trending": "open_source",
    "github_releases": "open_source",
    "awesome_lists": "open_source",
    "hackernews": "startups",
    "lobsters": "programming",
    "reddit": "programming",
    "devto": "programming",
    "medium": "business",
    "hashnode": "programming",
    "stackoverflow": "programming",
    "stackoverflow_blog": "programming",
    "producthunt": "startups",
    "rss": "business",
    "google_news": "business",
    "cloudflare_blog": "cloud",
    "stripe_engineering": "programming",
    "vercel_blog": "cloud",
    "linear_blog": "startups",
    "netflix_tech_blog": "cloud",
    "uber_engineering": "programming",
    "shopify_engineering": "programming",
    "official_docs": "programming",
    "youtube": "business",
    "linkedin": "business",
    "x": "startups",
    "news_api": "business",
}


def default_source_specs() -> dict[str, SourceSpec]:
    specs: dict[str, SourceSpec] = {}
    for name in list_connectors():
        tier = SOURCE_TIERS.get(name, 2)
        category = _CATEGORY_BY_SOURCE.get(name, "programming")
        specs[name] = SourceSpec(
            name=name,
            authority_score=_authority_from_tier(tier),
            freshness_weight=_freshness_for(category, name),
            update_frequency=_frequency_for(name, category),
            category=category,
            trust_level=_trust_from_tier(tier),
            parser=name,
            tier=tier,
            enabled=True,
        )
    return specs


class SourceRegistry:
    """Curated source metadata + connector parser resolution."""

    def __init__(self, specs: dict[str, SourceSpec] | None = None) -> None:
        self._specs = dict(specs or default_source_specs())

    def list_names(self) -> list[str]:
        return sorted(self._specs)

    def get(self, name: str) -> SourceSpec:
        key = (name or "").strip().lower()
        if key not in self._specs:
            raise KeyError(f"Unknown source: {name}")
        return self._specs[key]

    def register(
        self,
        spec: SourceSpec,
        factory: Callable[[], BaseConnector] | None = None,
    ) -> None:
        """Register metadata and optionally hot-register a connector factory."""
        self._specs[spec.name.strip().lower()] = spec
        if factory is not None:
            register_connector(spec.parser or spec.name, factory)

    def by_category(self, category: str) -> list[SourceSpec]:
        cat = (category or "").strip().lower()
        return [s for s in self._specs.values() if s.category == cat and s.enabled]

    def enabled_parsers(self) -> list[str]:
        return sorted({s.parser for s in self._specs.values() if s.enabled})

    def resolve_parser(self, name: str) -> BaseConnector:
        spec = self.get(name)
        return get_connector(spec.parser)

    def as_dict(self) -> dict[str, Any]:
        return {name: spec.as_dict() for name, spec in sorted(self._specs.items())}


def list_sources() -> list[str]:
    return SourceRegistry().list_names()
