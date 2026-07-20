"""RSS Registry — curated feeds grouped by topic domain."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any


@dataclass(frozen=True)
class RSSFeed:
    name: str
    url: str
    category: str
    authority_score: float = 0.7
    notes: str = ""

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


RSS_CATEGORIES: tuple[str, ...] = (
    "AI",
    "Machine Learning",
    "Economics",
    "Finance",
    "Business",
    "Programming",
    "Open Source",
    "Cybersecurity",
    "Cloud",
    "Startups",
)


def _feeds() -> list[RSSFeed]:
    return [
        # AI
        RSSFeed("OpenAI Blog", "https://openai.com/blog/rss.xml", "AI", 0.95),
        RSSFeed("Anthropic News", "https://www.anthropic.com/rss.xml", "AI", 0.95),
        RSSFeed("DeepMind Blog", "https://deepmind.google/blog/rss.xml", "AI", 0.95),
        RSSFeed("Hugging Face Blog", "https://huggingface.co/blog/feed.xml", "AI", 0.9),
        RSSFeed("Google AI Blog", "https://blog.google/technology/ai/rss/", "AI", 0.9),
        # Machine Learning
        RSSFeed("arXiv cs.LG", "http://export.arxiv.org/rss/cs.LG", "Machine Learning", 0.95),
        RSSFeed("arXiv cs.CL", "http://export.arxiv.org/rss/cs.CL", "Machine Learning", 0.95),
        RSSFeed("Distill", "https://distill.pub/rss.xml", "Machine Learning", 0.9),
        RSSFeed("Fast.ai", "https://www.fast.ai/atom.xml", "Machine Learning", 0.85),
        RSSFeed("Towards Data Science", "https://towardsdatascience.com/feed", "Machine Learning", 0.65),
        # Economics
        RSSFeed("NBER Working Papers", "https://www.nber.org/rss/new.xml", "Economics", 0.92),
        RSSFeed("VoxEU", "https://cepr.org/voxeu/rss.xml", "Economics", 0.85),
        RSSFeed("Brookings", "https://www.brookings.edu/feed/", "Economics", 0.8),
        # Finance
        RSSFeed("FT Markets", "https://www.ft.com/markets?format=rss", "Finance", 0.88),
        RSSFeed("Bloomberg Markets", "https://feeds.bloomberg.com/markets/news.rss", "Finance", 0.88),
        RSSFeed("CoinDesk", "https://www.coindesk.com/arc/outboundfeeds/rss/", "Finance", 0.7),
        # Business
        RSSFeed("Harvard Business Review", "https://hbr.org/feed", "Business", 0.85),
        RSSFeed("a16z Blog", "https://a16z.com/feed/", "Business", 0.8),
        RSSFeed("First Round Review", "https://review.firstround.com/feed.xml", "Business", 0.8),
        # Programming
        RSSFeed("Stack Overflow Blog", "https://stackoverflow.blog/feed/", "Programming", 0.82),
        RSSFeed("Dev.to", "https://dev.to/feed", "Programming", 0.7),
        RSSFeed("Lobsters", "https://lobste.rs/rss", "Programming", 0.8),
        RSSFeed("Stripe Engineering", "https://stripe.com/blog/feed.rss", "Programming", 0.88),
        RSSFeed("Uber Engineering", "https://www.uber.com/blog/engineering/rss/", "Programming", 0.85),
        # Open Source
        RSSFeed("GitHub Blog", "https://github.blog/feed/", "Open Source", 0.9),
        RSSFeed("Changelog", "https://changelog.com/feed", "Open Source", 0.8),
        RSSFeed("LWN.net", "https://lwn.net/headlines/rss", "Open Source", 0.9),
        # Cybersecurity
        RSSFeed("Krebs on Security", "https://krebsonsecurity.com/feed/", "Cybersecurity", 0.9),
        RSSFeed("The Hacker News", "https://feeds.feedburner.com/TheHackersNews", "Cybersecurity", 0.75),
        RSSFeed("Google Project Zero", "https://googleprojectzero.blogspot.com/feeds/posts/default", "Cybersecurity", 0.95),
        # Cloud
        RSSFeed("Cloudflare Blog", "https://blog.cloudflare.com/rss/", "Cloud", 0.9),
        RSSFeed("AWS Architecture", "https://aws.amazon.com/blogs/architecture/feed/", "Cloud", 0.88),
        RSSFeed("Vercel Blog", "https://vercel.com/atom", "Cloud", 0.8),
        RSSFeed("Netflix Tech Blog", "https://netflixtechblog.com/feed", "Cloud", 0.88),
        # Startups
        RSSFeed("Y Combinator Blog", "https://www.ycombinator.com/blog/rss/", "Startups", 0.85),
        RSSFeed("TechCrunch Startups", "https://techcrunch.com/category/startups/feed/", "Startups", 0.75),
        RSSFeed("Product Hunt", "https://www.producthunt.com/feed", "Startups", 0.7),
        RSSFeed("Linear Blog", "https://linear.app/rss/changelog", "Startups", 0.75),
    ]


class RSSRegistry:
    """Curated RSS feeds grouped by category."""

    def __init__(self, feeds: list[RSSFeed] | None = None) -> None:
        self._feeds = list(feeds or _feeds())

    def categories(self) -> list[str]:
        return list(RSS_CATEGORIES)

    def all_feeds(self) -> list[RSSFeed]:
        return list(self._feeds)

    def by_category(self, category: str) -> list[RSSFeed]:
        key = (category or "").strip().lower()
        return [f for f in self._feeds if f.category.lower() == key]

    def register(self, feed: RSSFeed) -> None:
        self._feeds.append(feed)

    def urls(self, category: str | None = None) -> list[str]:
        feeds = self.by_category(category) if category else self._feeds
        return [f.url for f in feeds]

    def as_dict(self) -> dict[str, list[dict[str, Any]]]:
        out: dict[str, list[dict[str, Any]]] = {c: [] for c in RSS_CATEGORIES}
        for feed in self._feeds:
            out.setdefault(feed.category, []).append(feed.as_dict())
        return out


def list_rss_categories() -> list[str]:
    return list(RSS_CATEGORIES)
