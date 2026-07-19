"""Copy editor — mechanical prose issues (never rewrites)."""

from __future__ import annotations

import re

from agents.editor._text import (
    clamp100,
    first_sentence,
    generic_hits,
    last_sentence,
    normalize,
    overused_transition_hits,
    passive_hits,
    phrase_ngrams,
    sentences,
    weak_verb_ratio,
    word_freq,
    words,
)
from agents.editor.schemas import CheckReport, EditorialIssue, Severity
from shared.quality import scan_text


class CopyEditor:
    name = "copy_editor"

    def check(self, text: str, *, user_memory: dict | None = None) -> CheckReport:
        text = normalize(text)
        issues: list[EditorialIssue] = []
        score = 88
        scan = scan_text(text, user_memory)

        # Repeated phrases / words
        for phrase, c in phrase_ngrams(text, 3).most_common(6):
            if c >= 2 and len(phrase) > 10:
                issues.append(
                    EditorialIssue(
                        code="REPEATED_PHRASE",
                        category="copy",
                        severity=Severity.MINOR,
                        problem=f"Repeated phrase '{phrase}' ({c}x).",
                        why="Echoed phrases look unedited.",
                        suggestion="Keep one instance; cut the rest.",
                    )
                )
                score -= 5
                break
        for w, c in word_freq(text).most_common(5):
            if c >= 5 and w not in {"that", "with", "this", "from"}:
                issues.append(
                    EditorialIssue(
                        code="REPEATED_WORD",
                        category="copy",
                        severity=Severity.INFO,
                        problem=f"Repeated word '{w}' ({c}x).",
                        why="High repetition dulls rhythm.",
                        suggestion="Vary wording where meaning allows.",
                    )
                )
                score -= 3
                break

        long = [s for s in sentences(text) if len(words(s)) > 28]
        for s in long[:2]:
            issues.append(
                EditorialIssue(
                    code="LONG_SENTENCE",
                    category="copy",
                    severity=Severity.MINOR,
                    location=s[:100],
                    problem="Long sentence detected.",
                    why="Length increases cognitive load.",
                    suggestion="Split after the main clause.",
                )
            )
            score -= 6

        passives = passive_hits(text)
        if len(passives) >= 2:
            issues.append(
                EditorialIssue(
                    code="PASSIVE_VOICE",
                    category="copy",
                    severity=Severity.MINOR,
                    problem=f"Passive constructions found (e.g. '{passives[0]}').",
                    why="Passive voice obscures agency and weakens authority.",
                    suggestion="Prefer active verbs naming the actor when known.",
                )
            )
            score -= 8

        if weak_verb_ratio(text) > 0.22:
            issues.append(
                EditorialIssue(
                    code="WEAK_VERBS",
                    category="copy",
                    severity=Severity.MINOR,
                    problem="High density of weak verbs (is/are/have/get/make).",
                    why="Weak verbs flatten prose and hide action.",
                    suggestion="Swap in precise verbs already implied by the content.",
                )
            )
            score -= 8

        generics = generic_hits(text)
        if generics:
            issues.append(
                EditorialIssue(
                    code="GENERIC_EXPR",
                    category="copy",
                    severity=Severity.MAJOR if len(generics) >= 3 else Severity.MINOR,
                    problem=f"Generic expressions: {', '.join(generics[:5])}.",
                    why="Generic diction fails serious editorial standards.",
                    suggestion="Delete or replace with concrete terms from the draft.",
                )
            )
            score -= min(18, 6 * len(generics))

        overused = overused_transition_hits(text)
        if overused:
            issues.append(
                EditorialIssue(
                    code="OVERUSED_TRANSITIONS",
                    category="copy",
                    severity=Severity.MINOR,
                    problem=f"Overused transitions: {', '.join(overused)}.",
                    why="Stock transitions are a hallmark of unedited AI drafts.",
                    suggestion="Use a sharper contrast tied to the argument.",
                )
            )
            score -= 7

        opening = first_sentence(text)
        if scan.has_weak_hook or (opening and len(words(opening)) < 4):
            issues.append(
                EditorialIssue(
                    code="WEAK_OPENING",
                    category="copy",
                    severity=Severity.MAJOR,
                    location=opening[:100],
                    problem="Weak opening.",
                    why="Readers decide in the first line whether to continue.",
                    suggestion="Lead with a specific tension already in the body.",
                )
            )
            score -= 12

        ending = last_sentence(text)
        weak_end = bool(
            re.search(
                r"\b(thoughts\??|thanks for reading|in conclusion|that's it)\b",
                ending,
                re.I,
            )
        ) or (ending and len(words(ending)) < 3)
        if weak_end:
            issues.append(
                EditorialIssue(
                    code="WEAK_ENDING",
                    category="copy",
                    severity=Severity.MINOR,
                    location=ending[:100],
                    problem="Weak ending.",
                    why="Soft landings dissipate authority and practical usefulness.",
                    suggestion="End on an implication, decision rule, or precise question.",
                )
            )
            score -= 10

        # Light grammar heuristics (deterministic)
        if re.search(r"\s{2,}", text.replace("\n", " ")):
            issues.append(
                EditorialIssue(
                    code="GRAMMAR",
                    category="copy",
                    severity=Severity.INFO,
                    problem="Irregular spacing detected.",
                    why="Spacing artifacts look unprofessional.",
                    suggestion="Normalize spaces before publish.",
                )
            )
            score -= 2
        if re.search(r"\b(alot|recieve|seperate|occured)\b", text, re.I):
            issues.append(
                EditorialIssue(
                    code="GRAMMAR",
                    category="copy",
                    severity=Severity.MINOR,
                    problem="Likely misspelling detected.",
                    why="Spelling errors reduce trust.",
                    suggestion="Correct the misspelling before approval.",
                )
            )
            score -= 8

        return CheckReport(name=self.name, score=clamp100(score), issues=issues)
