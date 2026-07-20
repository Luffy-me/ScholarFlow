"""Schemas for Research Intelligence."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class EvidenceClaim(BaseModel):
    claim: str
    supporting_sources: list[str] = Field(default_factory=list)
    contradicting_sources: list[str] = Field(default_factory=list)
    confidence: float = 0.0
    last_verified: str = ""
    verified: bool = False


class TrendSignal(BaseModel):
    trend: str
    momentum: float = 0.0
    confidence: float = 0.0
    source_count: int = 0
    supporting_sources: list[str] = Field(default_factory=list)


class RankedSource(BaseModel):
    id: str
    title: str
    url: str = ""
    tier: int = 2
    score: float = 0.0
    source_type: str = ""
    snippet: str = ""


class ResearchBrief(BaseModel):
    topic: str
    sources: list[RankedSource] = Field(default_factory=list)
    evidence: list[EvidenceClaim] = Field(default_factory=list)
    trends: list[TrendSignal] = Field(default_factory=list)
    summary: str = ""
    open_questions: list[str] = Field(default_factory=list)
    connector_stats: dict[str, int] = Field(default_factory=dict)
    offline: bool = True

    def as_dict(self) -> dict[str, Any]:
        return self.model_dump()
