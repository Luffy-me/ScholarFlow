"""Detect recurring discussions, pain points, and emerging themes."""

from __future__ import annotations

import re
from collections import Counter

from agents.research.schemas import TrendSignal
from connectors.base import SourceDocument
from models.capabilities import Capability


_PAIN = re.compile(r"\b(pain point|frustrat|broken|slow|noise|generic|hype|tradeoff|bottleneck)\b", re.I)
_GROWTH = re.compile(r"\b(emerging|rising|rapid|growth|shift|momentum)\b", re.I)
_FAQ = re.compile(r"\b(how (do|to)|why (does|is)|what (is|are)|should I)\b", re.I)


class TrendDetector:
    name = "trend_detector"
    capabilities = [Capability.TREND_DETECTION]

    def detect(self, documents: list[SourceDocument], *, topic: str = "") -> list[TrendSignal]:
        if not documents:
            return []

        token_counts: Counter[str] = Counter()
        pain_hits = 0
        growth_hits = 0
        faq_hits = 0
        for doc in documents:
            blob = f"{doc.title} {doc.snippet} {doc.content}"
            for tok in re.findall(r"[a-zA-Z]{4,}", blob.lower()):
                if tok in {"this", "that", "with", "from", "about", "local", "fixture"}:
                    continue
                token_counts[tok] += 1
            pain_hits += len(_PAIN.findall(blob))
            growth_hits += len(_GROWTH.findall(blob))
            faq_hits += len(_FAQ.findall(blob))

        source_ids = [d.id for d in documents if d.id]
        source_count = len(documents)
        top_terms = [t for t, _ in token_counts.most_common(5)]
        theme = " / ".join(top_terms[:3]) if top_terms else (topic or "general discussion")

        signals = [
            TrendSignal(
                trend=f"Recurring discussion: {theme}",
                momentum=min(1.0, 0.35 + source_count * 0.05 + growth_hits * 0.08),
                confidence=min(1.0, 0.4 + source_count * 0.04),
                source_count=source_count,
                supporting_sources=source_ids[:8],
            ),
            TrendSignal(
                trend="Developer pain points around workflow quality and generic advice",
                momentum=min(1.0, 0.3 + pain_hits * 0.1),
                confidence=min(1.0, 0.35 + pain_hits * 0.08),
                source_count=source_count,
                supporting_sources=source_ids[:8],
            ),
            TrendSignal(
                trend="Frequently asked operational questions",
                momentum=min(1.0, 0.25 + faq_hits * 0.12),
                confidence=min(1.0, 0.3 + faq_hits * 0.1),
                source_count=source_count,
                supporting_sources=source_ids[:8],
            ),
        ]
        # Keep strongest first
        signals.sort(key=lambda s: (-s.momentum, -s.confidence))
        return signals
