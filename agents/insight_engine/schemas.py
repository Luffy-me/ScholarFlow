"""Schemas for the Insight Engine (DeepSeek reasoning)."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field, field_validator

from agents.base import AgentInput, AgentOutput
from shared.quality import clamp_score


class Insight(BaseModel):
    hidden_pattern: str = ""
    common_belief: str = ""
    contrarian_view: str = ""
    why_it_matters: str = ""
    supporting_reasoning: str = ""
    reader_takeaway: str = ""
    originality_score: int = 0

    # Backward-compatible aliases used by older tests / pipeline consumers.
    @property
    def core_insight(self) -> str:
        return self.hidden_pattern

    @property
    def new_perspective(self) -> str:
        return self.contrarian_view

    @property
    def supporting_evidence(self) -> str:
        return self.supporting_reasoning

    @field_validator("originality_score", mode="before")
    @classmethod
    def _clamp_originality(cls, value: Any) -> int:
        try:
            return clamp_score(value)
        except (TypeError, ValueError):
            return 0

    def as_dict(self) -> dict[str, Any]:
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
