"""Shared deterministic text utilities for editorial review."""

from __future__ import annotations

import re
from collections import Counter


_SENTENCE_SPLIT = re.compile(r"(?<=[.!?])\s+")
_WORD = re.compile(r"[A-Za-z']+")
_PASSIVE = re.compile(
    r"\b(is|are|was|were|be|been|being)\s+(\w+ed|shown|made|given|taken|seen|done|built|found)\b",
    re.I,
)
_WEAK_VERBS = {
    "is",
    "are",
    "was",
    "were",
    "be",
    "been",
    "being",
    "have",
    "has",
    "had",
    "do",
    "does",
    "did",
    "get",
    "got",
    "make",
    "made",
    "seem",
    "seems",
}
_GENERIC = {
    "synergy",
    "leverage",
    "unlock",
    "revolutionize",
    "game-changer",
    "cutting-edge",
    "robust",
    "seamless",
    "innovative",
    "landscape",
    "paradigm",
    "holistic",
    "utilize",
}
_OVERUSED_TRANSITIONS = {
    "furthermore",
    "moreover",
    "additionally",
    "in conclusion",
    "it goes without saying",
    "at the end of the day",
    "needless to say",
}


def normalize(text: str) -> str:
    return (text or "").replace("\r\n", "\n").strip()


def sentences(text: str) -> list[str]:
    body = re.sub(r"\s+", " ", normalize(text).replace("\n", " "))
    if not body:
        return []
    parts = [p.strip() for p in _SENTENCE_SPLIT.split(body) if p.strip()]
    return parts or [body]


def paragraphs(text: str) -> list[str]:
    return [p.strip() for p in re.split(r"\n\s*\n", normalize(text)) if p.strip()]


def words(text: str) -> list[str]:
    return _WORD.findall(text or "")


def word_count(text: str) -> int:
    return len(words(text))


def clamp100(value: float) -> int:
    return max(0, min(100, int(round(value))))


def mean(values: list[float]) -> float:
    return sum(values) / len(values) if values else 0.0


def first_sentence(text: str) -> str:
    s = sentences(text)
    return s[0] if s else ""


def last_sentence(text: str) -> str:
    s = sentences(text)
    return s[-1] if s else ""


def word_freq(text: str) -> Counter[str]:
    return Counter(w.lower() for w in words(text) if len(w) > 3)


def phrase_ngrams(text: str, n: int = 3) -> Counter[str]:
    toks = [w.lower() for w in words(text)]
    grams: list[str] = []
    for i in range(max(0, len(toks) - n + 1)):
        grams.append(" ".join(toks[i : i + n]))
    return Counter(grams)


def passive_hits(text: str) -> list[str]:
    return [m.group(0) for m in _PASSIVE.finditer(text or "")]


def weak_verb_ratio(text: str) -> float:
    toks = [w.lower() for w in words(text)]
    if not toks:
        return 0.0
    weak = sum(1 for t in toks if t in _WEAK_VERBS)
    return weak / len(toks)


def generic_hits(text: str) -> list[str]:
    toks = {w.lower() for w in words(text)}
    return sorted(toks & _GENERIC)


def overused_transition_hits(text: str) -> list[str]:
    low = (text or "").lower()
    return [t for t in sorted(_OVERUSED_TRANSITIONS) if t in low]


def has_transition_glue(text: str) -> bool:
    return bool(
        re.search(
            r"\b(because|however|instead|but|so|therefore|while|what changed|trade-?off)\b",
            text or "",
            re.I,
        )
    )


def tense_markers(text: str) -> dict[str, int]:
    low = (text or "").lower()
    past = len(re.findall(r"\b(\w+ed|was|were|had)\b", low))
    present = len(re.findall(r"\b(is|are|am|do|does|can|will)\b", low))
    future = len(re.findall(r"\b(will|going to|won't)\b", low))
    return {"past": past, "present": present, "future": future}


def statistic_claims(text: str) -> list[str]:
    return [
        m.group(0)
        for m in re.finditer(
            r"\b\d+(\.\d+)?\s*(%|percent|x|million|billion|users|customers)?\b",
            text or "",
            re.I,
        )
    ]
