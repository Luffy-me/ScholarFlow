"""Truth Layer v2 — verify first-person claims against user_memory.json."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any, Literal

from pydantic import BaseModel, Field

from agents.base import Agent, AgentInput, AgentOutput
from models.base import ModelProvider
from shared.knowledge import allowed_experience_texts, load_user_memory


ClaimType = Literal[
    "project",
    "client",
    "metric",
    "achievement",
    "quote",
    "time_reference",
    "personal_experience",
]


class Claim(BaseModel):
    text: str
    claim_type: ClaimType
    reason: str = ""


class ClaimCheckResult(BaseModel):
    approved_claims: list[Claim] = Field(default_factory=list)
    rejected_claims: list[Claim] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    safe: bool = True
    sanitized_text: str = ""


class GroundingInput(AgentInput):
    pass


class GroundingOutput(AgentOutput):
    approved_claims: list[dict[str, Any]] = Field(default_factory=list)
    rejected_claims: list[dict[str, Any]] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    safe: bool = True


_SENTENCE_SPLIT = re.compile(r"(?<=[.!?])\s+|\n+")
_FIRST_PERSON = re.compile(r"\b(I|I'm|I've|I'd|me|my|mine|we|we're|we've|our|us)\b", re.I)

# High-risk unsupported claim detectors (checked before memory grounding).
_CLIENT_RE = re.compile(
    r"\b(for a client|my client|our client|clients said|a real user said|customer said)\b",
    re.I,
)
_METRIC_RE = re.compile(
    r"\b("
    r"\d+\s*%|"
    r"retention jumped by|"
    r"grew by \d+|"
    r"increased by \d+|"
    r"failed \d+%|"
    r"million[- ]user|"
    r"thousands of (customers|users)|"
    r"\$\d+[MmBb]?"
    r")\b",
    re.I,
)
_QUOTE_RE = re.compile(r"[“\"]([^”\"]{8,})[”\"]")
_TIME_RE = re.compile(
    r"\b("
    r"last week|yesterday|this morning|two days ago|a week ago|"
    r"last month|last quarter|last year|"
    r"spent a week|in \d+ days|over the weekend"
    r")\b",
    re.I,
)
_ACHIEVEMENT_RE = re.compile(
    r"\b("
    r"I (built|shipped|launched|raised|hired|scaled)|"
    r"we (built|shipped|launched|scaled|introduced)|"
    r"I showed it to"
    r")\b",
    re.I,
)
_PROJECT_HINT_RE = re.compile(
    r"\b(RAG chatbot|LinkedIn Content Intelligence Engine|local RAG|evaluation loop|local AI)\b",
    re.I,
)


@dataclass
class _MemoryIndex:
    raw: dict[str, Any]
    allowed: list[str]
    allowed_l: list[str]
    projects_l: list[str]
    experiences_l: list[str]
    skills_l: list[str]
    background_l: list[str]

    @classmethod
    def from_memory(cls, memory: dict[str, Any]) -> "_MemoryIndex":
        allowed = allowed_experience_texts(memory)
        return cls(
            raw=memory,
            allowed=allowed,
            allowed_l=[a.lower() for a in allowed],
            projects_l=[str(p).lower() for p in memory.get("projects") or []],
            experiences_l=[str(e).lower() for e in memory.get("experiences") or []],
            skills_l=[str(s).lower() for s in memory.get("skills") or []],
            background_l=[str(b).lower() for b in memory.get("background") or []],
        )

    def mentions_allowed(self, text: str) -> bool:
        t = text.lower()
        return any(item and item in t for item in self.allowed_l)

    def mentions_project(self, text: str) -> bool:
        t = text.lower()
        return any(p and p in t for p in self.projects_l)


def _split_sentences(text: str) -> list[str]:
    parts = [p.strip() for p in _SENTENCE_SPLIT.split(text.strip()) if p.strip()]
    return parts


def _is_first_person_claim(sentence: str) -> bool:
    return bool(_FIRST_PERSON.search(sentence))


def _classify_and_judge(sentence: str, memory: _MemoryIndex) -> tuple[Claim | None, Claim | None, list[str]]:
    """Return (approved, rejected, warnings) for one sentence. At most one of approved/rejected."""
    warnings: list[str] = []
    if not _is_first_person_claim(sentence):
        # Non-first-person quotes can still be fake dialogue attributed nearby.
        if _QUOTE_RE.search(sentence) and re.search(r"\b(said|told me|they said)\b", sentence, re.I):
            return None, Claim(
                text=sentence,
                claim_type="quote",
                reason="Fabricated user/client quote is not present in user_memory.json",
            ), warnings
        return None, None, warnings

    # Fake clients — never allowed unless explicitly stored in memory as an experience string.
    if _CLIENT_RE.search(sentence):
        if not any("client" in item for item in memory.allowed_l):
            return None, Claim(
                text=sentence,
                claim_type="client",
                reason="Client/user anecdote is not present in user_memory.json",
            ), warnings

    # Fake metrics / numbers tied to personal outcome — require exact memory support.
    if _METRIC_RE.search(sentence):
        metric_match = _METRIC_RE.search(sentence)
        metric_text = metric_match.group(0) if metric_match else ""
        exact = any(metric_text.lower() in item for item in memory.allowed_l)
        if not exact:
            return None, Claim(
                text=sentence,
                claim_type="metric",
                reason="Numeric/performance claim is not present in user_memory.json",
            ), warnings

    # Fake quotes in first-person narrative.
    if _QUOTE_RE.search(sentence) and re.search(r"\b(said|told me|they said|user said)\b", sentence, re.I):
        return None, Claim(
            text=sentence,
            claim_type="quote",
            reason="Quoted dialogue is not present in user_memory.json",
        ), warnings

    # Specific time references are high-risk unless the phrase itself is in memory.
    if _TIME_RE.search(sentence):
        time_match = _TIME_RE.search(sentence)
        time_text = time_match.group(0).lower() if time_match else ""
        if not any(time_text and time_text in item for item in memory.allowed_l):
            return None, Claim(
                text=sentence,
                claim_type="time_reference",
                reason="Specific time reference is not grounded in user_memory.json",
            ), warnings

    # Achievements / built-X claims must map to known projects/experiences.
    if _ACHIEVEMENT_RE.search(sentence) or re.search(r"\bI (built|worked on|tested|compared)\b", sentence, re.I):
        if memory.mentions_project(sentence) or memory.mentions_allowed(sentence):
            return (
                Claim(
                    text=sentence,
                    claim_type="project" if memory.mentions_project(sentence) else "personal_experience",
                    reason="Grounded in user_memory.json",
                ),
                None,
                warnings,
            )
        # Achievement-like but ungrounded.
        if _ACHIEVEMENT_RE.search(sentence):
            return None, Claim(
                text=sentence,
                claim_type="achievement",
                reason="Achievement/project claim is not present in user_memory.json",
            ), warnings
        warnings.append(f"First-person statement lacks explicit memory anchor: {sentence[:120]}")
        return (
            Claim(text=sentence, claim_type="personal_experience", reason="Generic first-person; no hard contradiction"),
            None,
            warnings,
        )

    # Project mentions
    if _PROJECT_HINT_RE.search(sentence) or memory.mentions_project(sentence):
        if memory.mentions_project(sentence) or memory.mentions_allowed(sentence):
            return (
                Claim(text=sentence, claim_type="project", reason="Project grounded in user_memory.json"),
                None,
                warnings,
            )
        return None, Claim(
            text=sentence,
            claim_type="project",
            reason="Project mention is not present in user_memory.json",
        ), warnings

    # Default: first-person without hard-risk patterns — approve with optional warning.
    if len(sentence) > 20:
        return (
            Claim(text=sentence, claim_type="personal_experience", reason="No unsupported hard-risk markers"),
            None,
            warnings,
        )
    return None, None, warnings


def check_claims(text: str, memory: dict[str, Any] | None = None) -> ClaimCheckResult:
    mem = _MemoryIndex.from_memory(memory or load_user_memory())
    approved: list[Claim] = []
    rejected: list[Claim] = []
    warnings: list[str] = []

    for sentence in _split_sentences(text):
        ok, bad, warns = _classify_and_judge(sentence, mem)
        warnings.extend(warns)
        if ok:
            approved.append(ok)
        if bad:
            rejected.append(bad)

    return ClaimCheckResult(
        approved_claims=approved,
        rejected_claims=rejected,
        warnings=list(dict.fromkeys(warnings)),
        safe=len(rejected) == 0,
        sanitized_text=text,
    )


def sanitize_ungrounded_claims(text: str, memory: dict[str, Any] | None = None) -> ClaimCheckResult:
    """Remove rejected claim sentences and return grounding result for the sanitized text."""
    mem = _MemoryIndex.from_memory(memory or load_user_memory())
    kept: list[str] = []
    rejected: list[Claim] = []
    approved: list[Claim] = []
    warnings: list[str] = []

    for sentence in _split_sentences(text):
        ok, bad, warns = _classify_and_judge(sentence, mem)
        warnings.extend(warns)
        if bad:
            rejected.append(bad)
            continue
        kept.append(sentence)
        if ok:
            approved.append(ok)

    sanitized = " ".join(kept)
    sanitized = re.sub(r"\s{2,}", " ", sanitized).strip()
    if not sanitized:
        # Fallback grounded scaffold — never reintroduce rejected claims.
        projects = mem.raw.get("projects") or []
        project = projects[0] if projects else "recent work"
        sanitized = (
            f"I keep returning to lessons from {project}. "
            "I want specificity without inventing clients, metrics, or timelines."
        )
        warnings.append("Draft emptied after removing ungrounded claims; inserted grounded scaffold")
    # Re-check sanitized text for residual issues.
    residual = check_claims(sanitized, mem.raw)
    # Preserve originally rejected claims in the report.
    all_rejected = rejected + [
        c for c in residual.rejected_claims if c.text not in {r.text for r in rejected}
    ]
    return ClaimCheckResult(
        approved_claims=residual.approved_claims or approved,
        rejected_claims=all_rejected,
        warnings=list(dict.fromkeys(warnings + residual.warnings)),
        safe=len(residual.rejected_claims) == 0,
        sanitized_text=sanitized,
    )


class ClaimCheckerAgent(Agent[GroundingInput, GroundingOutput]):
    """Deterministic grounding agent (no LLM required)."""

    name = "claim_checker"

    def __init__(self, provider: ModelProvider | None = None) -> None:
        # Provider unused for scoring; Agent interface still expects one.
        from models.fake import FakeProvider

        super().__init__(provider or FakeProvider())

    async def run(self, payload: GroundingInput) -> GroundingOutput:
        memory = payload.user_memory or load_user_memory()
        result = sanitize_ungrounded_claims(payload.text, memory)
        return GroundingOutput(
            text=result.sanitized_text,
            approved_claims=[c.model_dump() for c in result.approved_claims],
            rejected_claims=[c.model_dump() for c in result.rejected_claims],
            warnings=result.warnings,
            safe=result.safe,
            data={
                "approved_claims": [c.model_dump() for c in result.approved_claims],
                "rejected_claims": [c.model_dump() for c in result.rejected_claims],
                "warnings": result.warnings,
                "safe": result.safe,
            },
            meta={"agent": self.name, "deterministic": True},
        )


def claim_check_payload(text: str, memory: dict[str, Any] | None = None) -> dict[str, Any]:
    """API/CLI helper matching the required JSON shape."""
    result = check_claims(text, memory)
    return {
        "approved_claims": [c.model_dump() for c in result.approved_claims],
        "rejected_claims": [c.model_dump() for c in result.rejected_claims],
        "warnings": result.warnings,
        "safe": result.safe,
    }
