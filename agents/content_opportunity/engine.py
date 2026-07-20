"""Content Opportunity Engine — find topics worth writing."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field

from agents.research.schemas import ResearchBrief, TrendSignal
from models.capabilities import Capability


class ContentOpportunity(BaseModel):
    topic: str
    score: float = 0.0
    reason: str = ""
    recommended_angle: str = ""
    target_audience: str = ""
    metrics: dict[str, float] = Field(default_factory=dict)


class ContentOpportunityEngine:
    name = "content_opportunity"
    capabilities = [Capability.RANKING]

    def score_topic(
        self,
        topic: str,
        *,
        brief: ResearchBrief | None = None,
        audience: str = "builders",
    ) -> ContentOpportunity:
        trends = brief.trends if brief else []
        evidence = brief.evidence if brief else []
        sources = brief.sources if brief else []

        novelty = self._novelty(topic, trends)
        search_demand = min(1.0, 0.35 + len(sources) * 0.05)
        discussion = min(1.0, 0.3 + (trends[0].momentum if trends else 0.2))
        technical_depth = min(1.0, 0.25 + sum(1 for s in sources if s.tier == 1) * 0.12)
        business = 0.55 if any(k in topic.lower() for k in ("product", "market", "roi", "growth")) else 0.45
        reader_value = min(1.0, 0.4 + len([e for e in evidence if e.verified]) * 0.1 + discussion * 0.2)
        competition = 0.75 if topic.strip().lower() in {"ai", "artificial intelligence"} else 0.35

        # Higher competition lowers opportunity.
        score = (
            novelty * 0.18
            + search_demand * 0.12
            + discussion * 0.18
            + technical_depth * 0.15
            + business * 0.1
            + reader_value * 0.17
            + (1.0 - competition) * 0.1
        )
        angle = (
            trends[0].trend
            if trends
            else f"Constraint-first lesson on {topic}"
        )
        reason = (
            f"Scored from novelty={novelty:.2f}, discussion={discussion:.2f}, "
            f"depth={technical_depth:.2f}, competition={competition:.2f}."
        )
        return ContentOpportunity(
            topic=topic,
            score=round(score * 100, 1),
            reason=reason,
            recommended_angle=angle,
            target_audience=audience or "professionals",
            metrics={
                "novelty": round(novelty, 3),
                "search_demand": round(search_demand, 3),
                "discussion_potential": round(discussion, 3),
                "technical_depth": round(technical_depth, 3),
                "business_relevance": round(business, 3),
                "reader_value": round(reader_value, 3),
                "competition": round(competition, 3),
            },
        )

    def rank(
        self,
        topics: list[str],
        *,
        briefs: dict[str, ResearchBrief] | None = None,
        audience: str = "builders",
    ) -> list[ContentOpportunity]:
        briefs = briefs or {}
        scored = [
            self.score_topic(topic, brief=briefs.get(topic), audience=audience)
            for topic in topics
        ]
        scored.sort(key=lambda item: -item.score)
        return scored

    def _novelty(self, topic: str, trends: list[TrendSignal]) -> float:
        broad = topic.strip().lower() in {"ai", "artificial intelligence", "the future of ai"}
        if broad:
            return 0.2
        if trends and trends[0].momentum >= 0.6:
            return 0.75
        return 0.55
