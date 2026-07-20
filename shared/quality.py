"""Deterministic quality gates used by agents and tests."""

from __future__ import annotations

import re
from dataclasses import dataclass, field

from shared.knowledge import allowed_experience_texts, load_banned_patterns, load_user_memory


@dataclass
class PatternHit:
    kind: str
    matched: str
    detail: str


@dataclass
class QualityScanResult:
    banned_phrases: list[PatternHit] = field(default_factory=list)
    weak_hooks: list[PatternHit] = field(default_factory=list)
    fake_experiences: list[PatternHit] = field(default_factory=list)
    first_person_count: int = 0
    has_strong_first_person: bool = False

    @property
    def has_generic_ai(self) -> bool:
        return bool(self.banned_phrases)

    @property
    def has_weak_hook(self) -> bool:
        return bool(self.weak_hooks)

    @property
    def has_fake_experience(self) -> bool:
        return bool(self.fake_experiences)


_FIRST_PERSON_RE = re.compile(r"\b(I|I'm|I've|my|me|we|our)\b", re.IGNORECASE)


def _contains_ci(text: str, needle: str) -> bool:
    return needle.lower() in text.lower()


def _opening(text: str, max_chars: int = 180) -> str:
    first_line = text.strip().splitlines()[0] if text.strip() else ""
    return first_line[:max_chars]


def scan_text(text: str, memory: dict | None = None) -> QualityScanResult:
    banned = load_banned_patterns()
    result = QualityScanResult()
    opening = _opening(text)

    for phrase in banned.get("phrases", []):
        if _contains_ci(text, phrase):
            result.banned_phrases.append(
                PatternHit("banned_phrase", phrase, "Generic AI / corporate phrasing detected")
            )

    for phrase in banned.get("weak_hooks", []):
        if _contains_ci(opening, phrase):
            result.weak_hooks.append(
                PatternHit("weak_hook", phrase, "Opening hook looks weak or generic")
            )

    allowed = {item.lower() for item in allowed_experience_texts(memory or load_user_memory())}
    for pattern in banned.get("fake_experience_patterns", []):
        match = re.search(pattern, text, flags=re.IGNORECASE)
        if not match:
            continue
        matched = match.group(0)
        # Allow only if the matched claim is clearly grounded in memory text.
        grounded = any(matched.lower() in item or item in matched.lower() for item in allowed)
        if not grounded:
            # Also reject absolute fabricated scale claims even if loosely related.
            result.fake_experiences.append(
                PatternHit(
                    "fake_experience",
                    matched,
                    "Personal experience claim is not present in user_memory.json",
                )
            )

    pronouns = _FIRST_PERSON_RE.findall(text)
    result.first_person_count = len(pronouns)
    result.has_strong_first_person = result.first_person_count >= 2 and not result.has_generic_ai
    return result


def clamp_score(value: float) -> int:
    return max(0, min(100, int(round(value))))
