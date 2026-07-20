"""Unified quality score for articles/posts."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field

from agents.writing_quality import analyze_writing_quality
from shared.quality import clamp_score, scan_text


class QualityScore(BaseModel):
    truth: int = 0
    specificity: int = 0
    clarity: int = 0
    human_voice: int = 0
    originality: int = 0
    novelty: int = 0
    reader_value: int = 0
    discussion_potential: int = 0
    engagement: int = 0
    technical_accuracy: int = 0
    overall: int = 0
    details: dict[str, Any] = Field(default_factory=dict)

    def as_dict(self) -> dict[str, Any]:
        return self.model_dump()


class QualityScorer:
    name = "quality_scorer"

    def score(
        self,
        text: str,
        *,
        user_memory: dict[str, Any] | None = None,
        safe: bool = True,
        engagement_overall: int | None = None,
        insight_originality: int | None = None,
    ) -> QualityScore:
        scan = scan_text(text or "", user_memory)
        wq = analyze_writing_quality(text or "", user_memory=user_memory)

        truth = 85 if safe else 25
        if scan.has_fake_experience:
            truth = min(truth, 20)

        specificity = wq.specificity_score
        human_voice = wq.human_quality_score
        originality = max(wq.originality_score, insight_originality or 0)
        novelty = originality if originality else 40
        clarity = 75 if text and len(text.split()) > 20 else 40
        if scan.has_generic_ai:
            clarity = min(clarity, 45)
            human_voice = min(human_voice, 35)
            originality = min(originality, 30)

        reader_value = clamp_score((specificity + human_voice + clarity) / 3)
        discussion = 70 if "?" in (text or "") else 45
        engagement = engagement_overall if engagement_overall is not None else discussion
        technical = clamp_score(60 + (10 if any(k in (text or "").lower() for k in ("rag", "model", "eval", "api")) else 0))
        if scan.has_fake_experience:
            technical = min(technical, 35)

        overall = clamp_score(
            (
                truth
                + specificity
                + clarity
                + human_voice
                + originality
                + novelty
                + reader_value
                + discussion
                + engagement
                + technical
            )
            / 10
        )
        return QualityScore(
            truth=truth,
            specificity=specificity,
            clarity=clarity,
            human_voice=human_voice,
            originality=originality,
            novelty=novelty,
            reader_value=reader_value,
            discussion_potential=discussion,
            engagement=engagement,
            technical_accuracy=technical,
            overall=overall,
            details={
                "ai_pattern_risk": wq.ai_pattern_risk,
                "generic_ai": scan.has_generic_ai,
                "safe": safe,
            },
        )
