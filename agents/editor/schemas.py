"""Schemas for the Editorial Review Engine (critique only — never writes)."""

from __future__ import annotations

from enum import Enum
from typing import Any

from pydantic import BaseModel, Field

from agents.base import AgentInput, AgentOutput


class PublishDecision(str, Enum):
    APPROVE = "Approve"
    NEEDS_MINOR_REVISION = "Needs Minor Revision"
    NEEDS_MAJOR_REVISION = "Needs Major Revision"
    REJECT = "Reject"


class Severity(str, Enum):
    INFO = "info"
    MINOR = "minor"
    MAJOR = "major"
    CRITICAL = "critical"


class EditorialIssue(BaseModel):
    code: str
    category: str
    severity: Severity = Severity.MINOR
    location: str = ""
    problem: str
    why: str
    suggestion: str = ""


class EditorialSuggestion(BaseModel):
    category: str
    suggestion: str
    why: str
    priority: int = 3  # 1 highest


class EditorScore(BaseModel):
    clarity: int = 0
    trust: int = 0
    flow: int = 0
    novelty: int = 0
    evidence: int = 0
    readability: int = 0
    authority: int = 0
    originality: int = 0
    practicality: int = 0
    overall: int = 0
    dimensions: dict[str, int] = Field(default_factory=dict)

    def as_dict(self) -> dict[str, Any]:
        return self.model_dump()


class CheckReport(BaseModel):
    name: str
    score: int = 0
    issues: list[EditorialIssue] = Field(default_factory=list)
    notes: list[str] = Field(default_factory=list)


class EditorialReport(BaseModel):
    summary: str = ""
    scores: EditorScore = Field(default_factory=EditorScore)
    story: CheckReport = Field(default_factory=lambda: CheckReport(name="story"))
    clarity: CheckReport = Field(default_factory=lambda: CheckReport(name="clarity"))
    consistency: CheckReport = Field(default_factory=lambda: CheckReport(name="consistency"))
    credibility: CheckReport = Field(default_factory=lambda: CheckReport(name="credibility"))
    tone: CheckReport = Field(default_factory=lambda: CheckReport(name="tone"))
    redundancy: CheckReport = Field(default_factory=lambda: CheckReport(name="redundancy"))
    copy_edit: CheckReport = Field(default_factory=lambda: CheckReport(name="copy"))
    linkedin_friendliness: int = 0
    reading_fatigue: int = 0
    confidence: float = 0.0


class PublishGateResult(BaseModel):
    decision: PublishDecision = PublishDecision.NEEDS_MAJOR_REVISION
    rationale: list[str] = Field(default_factory=list)
    blocking_issues: list[str] = Field(default_factory=list)
    score_overall: int = 0


class EditorialResult(BaseModel):
    original_draft: str = ""
    editorial_report: EditorialReport = Field(default_factory=EditorialReport)
    issues: list[EditorialIssue] = Field(default_factory=list)
    suggestions: list[EditorialSuggestion] = Field(default_factory=list)
    approved_draft: str = ""
    publish_decision: PublishDecision = PublishDecision.NEEDS_MAJOR_REVISION
    gate: PublishGateResult = Field(default_factory=PublishGateResult)
    meta: dict[str, Any] = Field(default_factory=dict)

    def as_dict(self) -> dict[str, Any]:
        return self.model_dump()


class EditorInput(AgentInput):
    """Draft under review (+ optional evidence refs / memory)."""

    pass


class EditorOutput(AgentOutput):
    result: EditorialResult = Field(default_factory=EditorialResult)

    def as_report(self) -> dict[str, Any]:
        return self.result.as_dict()
