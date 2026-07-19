"""Schemas for the Insight Engine."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field

from agents.base import AgentInput, AgentOutput


class Insight(BaseModel):
    core_insight: str = ""
    why_it_matters: str = ""
    common_belief: str = ""
    new_perspective: str = ""
    supporting_evidence: str = ""
    reader_takeaway: str = ""

    def as_dict(self) -> dict[str, str]:
        return self.model_dump()


class InsightQuality(BaseModel):
    strength_score: int = 0
    is_weak: bool = True
    is_strong: bool = False
    has_belief_contrast: bool = False
    takeaway_actionable: bool = False
    flags: list[str] = Field(default_factory=list)


class InsightEngineInput(AgentInput):
    """Topic + optional research/trends/verified experiences."""

    pass


class InsightEngineOutput(AgentOutput):
    insight: Insight = Field(default_factory=Insight)
    quality: InsightQuality = Field(default_factory=InsightQuality)

    def as_report(self) -> dict[str, Any]:
        return {
            **self.insight.as_dict(),
            "quality": self.quality.model_dump(),
        }
