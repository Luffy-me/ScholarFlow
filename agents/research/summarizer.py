"""Summarize ranked research into a brief."""

from __future__ import annotations

from agents.research.schemas import EvidenceClaim, RankedSource, TrendSignal
from models.capabilities import Capability


class ResearchSummarizer:
    name = "research_summarizer"
    capabilities = [Capability.SUMMARIZATION]

    def summarize(
        self,
        *,
        topic: str,
        ranked: list[RankedSource],
        evidence: list[EvidenceClaim],
        trends: list[TrendSignal],
    ) -> tuple[str, list[str]]:
        top_titles = [r.title for r in ranked[:4]]
        verified = [e.claim for e in evidence if e.verified][:3]
        trend_line = trends[0].trend if trends else "No strong trend signal yet"
        summary = (
            f"Research brief on {topic}: {trend_line}. "
            f"Top sources: {'; '.join(top_titles) if top_titles else 'none'}. "
            f"Verified claims: {'; '.join(verified) if verified else 'none yet'}."
        )
        open_questions = [
            f"What constraint actually limits progress on {topic}?",
            "Which claims remain unverified and should stay attributed opinions?",
        ]
        return summary, open_questions
