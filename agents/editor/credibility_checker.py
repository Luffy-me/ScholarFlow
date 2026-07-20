"""Credibility checker — unsupported claims, invented stats/stories, weak evidence."""

from __future__ import annotations

import re
from typing import Any

from agents.editor._text import clamp100, normalize, statistic_claims
from agents.editor.schemas import CheckReport, EditorialIssue, Severity
from shared.quality import scan_text


class CredibilityChecker:
    name = "credibility_checker"

    def check(
        self,
        text: str,
        *,
        evidence_refs: list[str] | None = None,
        user_memory: dict[str, Any] | None = None,
    ) -> CheckReport:
        text = normalize(text)
        evidence_refs = evidence_refs or []
        issues: list[EditorialIssue] = []
        score = 78 if evidence_refs else 55
        scan = scan_text(text, user_memory)

        if scan.has_fake_experience:
            for hit in scan.fake_experiences:
                issues.append(
                    EditorialIssue(
                        code="NO_FAKE_EXPERIENCE",
                        category="credibility",
                        severity=Severity.CRITICAL,
                        location=hit.matched[:120],
                        problem="Fake or unverified personal experience claim.",
                        why=hit.detail,
                        suggestion="Remove the claim or ground it in verified user memory.",
                    )
                )
            score = min(score, 25)

        stats = statistic_claims(text)
        invented = []
        for stat in stats:
            # Allow simple percents/numbers only when evidence present; else flag scale claims
            if re.search(r"(million|billion|users|customers|10x|100x)", stat, re.I) and not evidence_refs:
                invented.append(stat)
            elif re.search(r"\b\d{2,}\s*%|\b\d+x\b", stat, re.I) and not evidence_refs:
                invented.append(stat)
        if invented:
            issues.append(
                EditorialIssue(
                    code="NO_INVENTED_STATS",
                    category="credibility",
                    severity=Severity.CRITICAL,
                    problem=f"Statistic(s) without evidence refs: {', '.join(invented[:4])}.",
                    why="Invented statistics are an integrity failure for an Editor-in-Chief desk.",
                    suggestion="Cite Evidence Graph sources or remove the number.",
                )
            )
            score = min(score, 30)

        # Story invention cues
        if re.search(r"\b(a client of mine|my friend at|unnamed company|fortune 500)\b", text, re.I):
            if not evidence_refs:
                issues.append(
                    EditorialIssue(
                        code="INVENTED_STORY",
                        category="credibility",
                        severity=Severity.CRITICAL,
                        problem="Anecdote appears unsourced.",
                        why="Unverified stories are treated as invention.",
                        suggestion="Drop the anecdote or attach a verifiable source/memory entry.",
                    )
                )
                score = min(score, 35)

        # Unsupported absolute claims
        if re.search(r"\b(always|never|guaranteed|everyone knows)\b", text, re.I) and not evidence_refs:
            issues.append(
                EditorialIssue(
                    code="UNSUPPORTED_CLAIM",
                    category="credibility",
                    severity=Severity.MAJOR,
                    problem="Absolute claim without evidence support.",
                    why="Absolutes require unusually strong evidence.",
                    suggestion="Qualify the claim or attach supporting Evidence Graph refs.",
                )
            )
            score -= 18

        if not evidence_refs and word_count_safe(text) > 40:
            issues.append(
                EditorialIssue(
                    code="EVIDENCE_REQUIRED",
                    category="credibility",
                    severity=Severity.MAJOR,
                    problem="No Evidence Graph references supplied for review.",
                    why="Without evidence, the desk cannot certify trustworthiness.",
                    suggestion="Attach supporting claim IDs/sources before publish review.",
                )
            )
            score -= 12
        elif evidence_refs:
            score = min(100, score + min(20, 4 * len(evidence_refs)))

        if score < 50 and not any(i.severity == Severity.CRITICAL for i in issues):
            issues.append(
                EditorialIssue(
                    code="WEAK_EVIDENCE",
                    category="credibility",
                    severity=Severity.MAJOR,
                    problem="Evidence quality is weak for publication.",
                    why="Authority depends on inspectable support, not confident tone.",
                    suggestion="Strengthen with verified claims or reduce assertive language.",
                )
            )

        return CheckReport(name=self.name, score=clamp100(score), issues=issues)


def word_count_safe(text: str) -> int:
    from agents.editor._text import word_count

    return word_count(text)
