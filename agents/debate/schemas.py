"""Schemas for Debate Mode (Qwen write ↔ DeepSeek critique)."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class DebateReview(BaseModel):
    generic_ideas: list[str] = Field(default_factory=list)
    weak_arguments: list[str] = Field(default_factory=list)
    missing_evidence: list[str] = Field(default_factory=list)
    originality_issues: list[str] = Field(default_factory=list)
    ai_writing_patterns: list[str] = Field(default_factory=list)
    improvements: list[str] = Field(default_factory=list)
    rejected: bool = False
    reject_reason: str = ""
    review_score: int = 0


class DebateFinalScore(BaseModel):
    final_score: int = 0
    originality_score: int = 0
    argument_strength: int = 0
    evidence_score: int = 0
    ai_pattern_risk: int = 0
    accepted: bool = False
    summary: str = ""


class DebateResult(BaseModel):
    enabled: bool = True
    draft_v1: str = ""
    review: DebateReview = Field(default_factory=DebateReview)
    draft_v2: str = ""
    final_score: DebateFinalScore = Field(default_factory=DebateFinalScore)
    generic_rejected: bool = False
    meta: dict[str, Any] = Field(default_factory=dict)
