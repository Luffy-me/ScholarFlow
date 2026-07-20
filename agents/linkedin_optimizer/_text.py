"""Deterministic text helpers for LinkedIn optimization (no fact invention)."""

from __future__ import annotations

import re
from statistics import pstdev


_SENTENCE_SPLIT = re.compile(r"(?<=[.!?])\s+")
_WORD = re.compile(r"[A-Za-z0-9']+")
_JARGON = {
    "synergy",
    "leverage",
    "paradigm",
    "ecosystem",
    "holistic",
    "disrupt",
    "unlock",
    "revolutionize",
    "game-changer",
    "cutting-edge",
    "utilize",
    "robust",
    "seamless",
    "scalable",
    "innovative",
}


def normalize(text: str) -> str:
    return (text or "").replace("\r\n", "\n").strip()


def lines(text: str) -> list[str]:
    return [ln.rstrip() for ln in normalize(text).split("\n")]


def non_empty_lines(text: str) -> list[str]:
    return [ln.strip() for ln in lines(text) if ln.strip()]


def first_two_lines(text: str) -> str:
    vals = non_empty_lines(text)[:2]
    return "\n".join(vals)


def first_sentence(text: str) -> str:
    body = normalize(text)
    if not body:
        return ""
    parts = _SENTENCE_SPLIT.split(body.replace("\n", " "), maxsplit=1)
    return parts[0].strip() if parts else body[:160]


def sentences(text: str) -> list[str]:
    body = re.sub(r"\s+", " ", normalize(text).replace("\n", " "))
    if not body:
        return []
    parts = [p.strip() for p in _SENTENCE_SPLIT.split(body) if p.strip()]
    return parts or [body]


def paragraphs(text: str) -> list[str]:
    chunks = re.split(r"\n\s*\n", normalize(text))
    return [c.strip() for c in chunks if c.strip()]


def words(text: str) -> list[str]:
    return _WORD.findall(text or "")


def word_count(text: str) -> int:
    return len(words(text))


def clamp01(value: float) -> float:
    return max(0.0, min(1.0, float(value)))


def clamp100(value: float) -> int:
    return max(0, min(100, int(round(value))))


def mean(values: list[float]) -> float:
    return sum(values) / len(values) if values else 0.0


def variety_score(lengths: list[int]) -> float:
    if len(lengths) < 2:
        return 0.35
    try:
        spread = pstdev(lengths)
    except Exception:  # noqa: BLE001
        spread = 0.0
    # Ideal: moderate variety
    return clamp01(spread / 12.0)


def jargon_density(text: str) -> float:
    toks = [w.lower() for w in words(text)]
    if not toks:
        return 0.0
    hits = sum(1 for w in toks if w in _JARGON)
    return clamp01(hits / max(8, len(toks)) * 8)


def has_question(text: str) -> bool:
    return "?" in (text or "")


def has_number(text: str) -> bool:
    return bool(re.search(r"\d", text or ""))


def has_specific_noun(text: str) -> bool:
    # Capitalized multi-char tokens beyond sentence start count as specificity signal
    toks = words(text)
    if len(toks) < 2:
        return False
    caps = [t for t in toks[1:] if t[:1].isupper() and len(t) > 2]
    return len(caps) >= 1 or has_number(text)


def preserve_body_after_hook(original: str, new_hook: str) -> str:
    """Replace the opening sentence only; keep the rest of the draft intact (intent/facts)."""
    original = normalize(original)
    new_hook = normalize(new_hook)
    if not original:
        return new_hook
    first = first_sentence(original)
    if not first:
        return new_hook
    idx = original.find(first)
    if idx < 0:
        # Fallback: keep everything after the first non-empty line
        body_lines = non_empty_lines(original)
        rest = "\n".join(body_lines[1:])
        return f"{new_hook}\n\n{rest}".strip() if rest else new_hook
    remainder = original[idx + len(first) :].lstrip(" \t\n")
    if not remainder:
        return new_hook
    return f"{new_hook}\n\n{remainder}".strip()


def ensure_paragraph_breaks(text: str, *, max_lines_per_block: int = 3) -> str:
    """Improve whitespace/scanning without changing words."""
    raw_lines = [ln.rstrip() for ln in normalize(text).split("\n")]
    if not raw_lines:
        return ""
    # If already has blank lines, keep structure mostly
    if any(not ln.strip() for ln in raw_lines):
        # collapse 3+ blanks to 1
        out: list[str] = []
        blank_run = 0
        for ln in raw_lines:
            if not ln.strip():
                blank_run += 1
                if blank_run == 1:
                    out.append("")
            else:
                blank_run = 0
                out.append(ln)
        return "\n".join(out).strip()

    # Insert a blank line every max_lines_per_block non-empty lines
    out = []
    count = 0
    for ln in raw_lines:
        if not ln.strip():
            continue
        out.append(ln)
        count += 1
        if count >= max_lines_per_block:
            out.append("")
            count = 0
    return "\n".join(out).strip()


def strip_trailing_hashtag_soup(text: str) -> str:
    """Remove excessive trailing hashtag blocks; keep content facts."""
    body = normalize(text)
    parts = body.split("\n")
    kept: list[str] = []
    for ln in parts:
        tags = re.findall(r"#\w+", ln)
        if tags and len(tags) >= 4 and len(words(re.sub(r"#\w+", "", ln))) <= 2:
            continue
        kept.append(ln)
    return "\n".join(kept).strip()
