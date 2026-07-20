"""Readability optimizer — length, speed, jargon, formatting."""

from __future__ import annotations

from agents.linkedin_optimizer._text import (
    clamp01,
    clamp100,
    jargon_density,
    mean,
    normalize,
    paragraphs,
    sentences,
    word_count,
    words,
)
from agents.linkedin_optimizer.schemas import ReadabilityReport


class ReadabilityOptimizer:
    name = "readability_optimizer"

    def analyze(self, text: str, *, wpm: float = 220.0) -> ReadabilityReport:
        text = normalize(text)
        sents = sentences(text)
        paras = paragraphs(text)
        wc = word_count(text)
        avg_sent = mean([float(len(words(s))) for s in sents]) if sents else 0.0
        avg_para = mean([float(len(words(p))) for p in paras]) if paras else float(wc)
        jargon = jargon_density(text)
        seconds = (wc / wpm) * 60.0 if wpm else 0.0

        formatting = 0.4
        if "\n\n" in text:
            formatting += 0.25
        if text.count("\n") >= 2:
            formatting += 0.15
        if not text.startswith(" "):
            formatting += 0.05
        if avg_para <= 55:
            formatting += 0.1
        formatting = clamp01(formatting)

        # Score components toward 100
        sent_score = 100 - abs(avg_sent - 14) * 4
        para_score = 100 - abs(avg_para - 40) * 1.2
        jargon_score = 100 - jargon * 100
        overall = clamp100(mean([sent_score, para_score, jargon_score, formatting * 100]))

        recs: list[str] = []
        if avg_sent > 22:
            recs.append("Shorten long sentences; aim near 12–16 words on average.")
        if avg_para > 70:
            recs.append("Split dense paragraphs for mobile readability.")
        if jargon > 0.15:
            recs.append("Reduce jargon density; prefer concrete operational language.")
        if formatting < 0.55:
            recs.append("Improve formatting with clearer line breaks and scannable blocks.")
        if seconds > 75:
            recs.append("Consider trimming length; estimated read time is high for feed scanning.")

        return ReadabilityReport(
            avg_sentence_length=round(avg_sent, 2),
            avg_paragraph_length=round(avg_para, 2),
            reading_speed_wpm=wpm,
            estimated_read_seconds=round(seconds, 1),
            jargon_density=round(jargon, 4),
            formatting_quality=round(formatting, 4),
            overall=overall,
            recommendations=recs,
        )
