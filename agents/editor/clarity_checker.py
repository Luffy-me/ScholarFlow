"""Clarity checker — sentence/paragraph rhythm, reading fatigue, transitions."""

from __future__ import annotations

from agents.editor._text import (
    clamp100,
    has_transition_glue,
    mean,
    normalize,
    overused_transition_hits,
    paragraphs,
    sentences,
    word_count,
    words,
)
from agents.editor.schemas import CheckReport, EditorialIssue, Severity


class ClarityChecker:
    name = "clarity_checker"

    def check(self, text: str) -> CheckReport:
        text = normalize(text)
        issues: list[EditorialIssue] = []
        sents = sentences(text)
        paras = paragraphs(text)
        lengths = [len(words(s)) for s in sents] or [0]
        avg_sent = mean([float(x) for x in lengths])
        avg_para = mean([float(len(words(p))) for p in paras]) if paras else float(word_count(text))
        score = 90

        long_sents = [s for s in sents if len(words(s)) > 28]
        if long_sents:
            issues.append(
                EditorialIssue(
                    code="SENTENCE_RHYTHM",
                    category="clarity",
                    severity=Severity.MINOR if len(long_sents) == 1 else Severity.MAJOR,
                    location=long_sents[0][:100],
                    problem=f"{len(long_sents)} sentence(s) exceed ~28 words.",
                    why="Long sentences raise reading fatigue and bury the point.",
                    suggestion="Split into a short claim + one supporting clause.",
                )
            )
            score -= min(24, 8 * len(long_sents))

        if avg_sent and (avg_sent < 7 or avg_sent > 22):
            issues.append(
                EditorialIssue(
                    code="SENTENCE_RHYTHM",
                    category="clarity",
                    severity=Severity.MINOR,
                    problem=f"Average sentence length is {avg_sent:.1f} words.",
                    why="Extreme averages hurt rhythm — either choppy or exhausting.",
                    suggestion="Aim near 12–18 words with intentional short punches.",
                )
            )
            score -= 8

        if avg_para > 70:
            issues.append(
                EditorialIssue(
                    code="PARAGRAPH_RHYTHM",
                    category="clarity",
                    severity=Severity.MAJOR,
                    problem=f"Average paragraph length is {avg_para:.0f} words.",
                    why="Dense paragraphs fail mobile scanning and increase fatigue.",
                    suggestion="Break into 2–4 line blocks with a single idea each.",
                )
            )
            score -= 16
        elif len(paras) <= 1 and word_count(text) > 80:
            issues.append(
                EditorialIssue(
                    code="PARAGRAPH_RHYTHM",
                    category="clarity",
                    severity=Severity.MINOR,
                    problem="Little/no paragraph whitespace.",
                    why="Wall-of-text formatting hurts LinkedIn friendliness.",
                    suggestion="Insert blank lines between beats.",
                )
            )
            score -= 10

        if word_count(text) >= 60 and not has_transition_glue(text):
            issues.append(
                EditorialIssue(
                    code="TRANSITIONS",
                    category="flow",
                    severity=Severity.MINOR,
                    problem="Few logical transitions (because / however / instead / trade-off).",
                    why="Without glue, the argument feels like a list of claims.",
                    suggestion="Add one causal or contrastive bridge between beats.",
                )
            )
            score -= 10

        overused = overused_transition_hits(text)
        if overused:
            issues.append(
                EditorialIssue(
                    code="TRANSITIONS",
                    category="copy",
                    severity=Severity.MINOR,
                    problem=f"Overused transitions: {', '.join(overused[:3])}.",
                    why="Stock transitions signal generic editorial quality.",
                    suggestion="Replace with concrete contrast grounded in the argument.",
                )
            )
            score -= 8

        # Reading fatigue proxy
        fatigue_penalty = 0
        if avg_sent > 20:
            fatigue_penalty += 10
        if avg_para > 60:
            fatigue_penalty += 12
        if len(long_sents) >= 2:
            fatigue_penalty += 10
        if fatigue_penalty:
            issues.append(
                EditorialIssue(
                    code="READING_FATIGUE",
                    category="clarity",
                    severity=Severity.MAJOR if fatigue_penalty >= 20 else Severity.MINOR,
                    problem="Reading fatigue risk is elevated.",
                    why="Fatigue reduces completion and perceived clarity.",
                    suggestion="Shorten the densest sentence and the longest paragraph first.",
                )
            )
            score -= fatigue_penalty

        return CheckReport(name=self.name, score=clamp100(score), issues=issues)
