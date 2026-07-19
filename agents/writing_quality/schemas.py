"""Schemas for the AI Writing Quality Analyzer."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field

from agents.base import AgentInput, AgentOutput


class DetectedPattern(BaseModel):
    category: str
    severity: str = "medium"
    example: str = ""
    explanation: str = ""


class WritingQualityInput(AgentInput):
    """Analyzer input: content + mode + verified memory facts."""

    content: str = ""
    verified_memory: list[str] = Field(default_factory=list)

    def resolved_content(self) -> str:
        return (self.content or self.text or "").strip()


class WritingQualityScores(BaseModel):
    human_quality_score: int = 0
    ai_pattern_risk: int = 0
    specificity_score: int = 0
    originality_score: int = 0


class WritingQualityOutput(AgentOutput):
    human_quality_score: int = 0
    ai_pattern_risk: int = 0
    specificity_score: int = 0
    originality_score: int = 0
    detected_patterns: list[DetectedPattern] = Field(default_factory=list)
    improvements: list[str] = Field(default_factory=list)

    def as_report(self) -> dict[str, Any]:
        return {
            "human_quality_score": self.human_quality_score,
            "ai_pattern_risk": self.ai_pattern_risk,
            "specificity_score": self.specificity_score,
            "originality_score": self.originality_score,
            "detected_patterns": [p.model_dump() for p in self.detected_patterns],
            "improvements": list(self.improvements),
        }
