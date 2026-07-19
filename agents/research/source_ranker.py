"""Rank sources by tier, confidence, and topical overlap."""

from __future__ import annotations

from agents.research.schemas import RankedSource
from connectors.base import SourceDocument
from models.capabilities import Capability


class SourceRanker:
    name = "research_ranker"
    capabilities = [Capability.RANKING]

    def rank(self, documents: list[SourceDocument], *, query: str = "") -> list[RankedSource]:
        q_tokens = {t for t in (query or "").lower().split() if len(t) > 2}
        ranked: list[RankedSource] = []
        for doc in documents:
            text = f"{doc.title} {doc.snippet} {doc.content}".lower()
            overlap = sum(1 for t in q_tokens if t in text)
            tier_bonus = {1: 0.35, 2: 0.15, 3: 0.0}.get(doc.tier, 0.1)
            score = float(doc.confidence) + tier_bonus + min(0.3, overlap * 0.05)
            ranked.append(
                RankedSource(
                    id=doc.id,
                    title=doc.title,
                    url=doc.url,
                    tier=doc.tier,
                    score=round(min(1.0, score), 3),
                    source_type=doc.source_type,
                    snippet=doc.snippet or doc.content[:220],
                )
            )
        ranked.sort(key=lambda item: (-item.score, item.tier, item.title))
        return ranked
