"""Tone reviewer — human authenticity, authority, LinkedIn friendliness."""

from __future__ import annotations

import re

from agents.editor._text import clamp100, first_sentence, generic_hits, normalize, paragraphs, word_count
from agents.editor.schemas import CheckReport, EditorialIssue, Severity
from shared.quality import scan_text


class ToneReviewer:
    name = "tone_reviewer"

    def check(self, text: str, *, user_memory: dict | None = None) -> CheckReport:
        text = normalize(text)
        issues: list[EditorialIssue] = []
        score = 82
        scan = scan_text(text, user_memory)

        if scan.has_generic_ai:
            issues.append(
                EditorialIssue(
                    code="ORIGINALITY",
                    category="tone",
                    severity=Severity.MAJOR,
                    problem="Generic AI / corporate phrasing detected.",
                    why="Commodity language fails Stripe/Linear/Anthropic editorial bars.",
                    suggestion="Delete filler and keep only concrete observations from the draft.",
                )
            )
            score -= 20

        generics = generic_hits(text)
        if generics:
            issues.append(
                EditorialIssue(
                    code="GENERIC_EXPR",
                    category="copy",
                    severity=Severity.MINOR,
                    problem=f"Generic expressions: {', '.join(generics[:5])}.",
                    why="These words rarely carry operator-specific meaning.",
                    suggestion="Replace with the specific constraint or result already in the piece.",
                )
            )
            score -= min(15, 5 * len(generics))

        if scan.has_weak_hook:
            issues.append(
                EditorialIssue(
                    code="WEAK_OPENING",
                    category="copy",
                    severity=Severity.MAJOR,
                    location=first_sentence(text)[:100],
                    problem="Weak or generic opening.",
                    why="The first line is the only guaranteed attention on LinkedIn.",
                    suggestion="Open on a specific tension already present later in the draft.",
                )
            )
            score -= 16

        # Human authenticity proxy
        if scan.first_person_count == 0 and word_count(text) > 60:
            issues.append(
                EditorialIssue(
                    code="HUMAN_VOICE",
                    category="tone",
                    severity=Severity.INFO,
                    problem="No first-person stance.",
                    why="A human point of view often increases authenticity — when true.",
                    suggestion="Only add first person if grounded in verified experience.",
                )
            )
        elif scan.has_strong_first_person and not scan.has_fake_experience:
            score += 8

        # LinkedIn friendliness
        if len(paragraphs(text)) <= 1 and word_count(text) > 90:
            issues.append(
                EditorialIssue(
                    code="LINKEDIN_SCAN",
                    category="linkedin",
                    severity=Severity.MINOR,
                    problem="Formatting is not feed-friendly.",
                    why="LinkedIn is scanned on mobile; walls of text underperform.",
                    suggestion="Use short paragraphs and a clear final question or implication.",
                )
            )
            score -= 10

        if re.search(r"(#\w+\s*){4,}", text):
            issues.append(
                EditorialIssue(
                    code="LINKEDIN_SCAN",
                    category="linkedin",
                    severity=Severity.MINOR,
                    problem="Hashtag soup detected.",
                    why="Excess tags look spammy and dilute authority.",
                    suggestion="Remove trailing hashtag blocks; keep at most 0–2 niche tags if needed.",
                )
            )
            score -= 8

        return CheckReport(name=self.name, score=clamp100(score), issues=issues)
