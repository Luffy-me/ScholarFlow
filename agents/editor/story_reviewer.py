"""Story reviewer — arc, logical flow, practical usefulness."""

from __future__ import annotations

import re

from agents.editor._text import clamp100, has_transition_glue, normalize, paragraphs, sentences, word_count
from agents.editor.schemas import CheckReport, EditorialIssue, Severity


class StoryReviewer:
    name = "story_reviewer"

    def check(self, text: str) -> CheckReport:
        text = normalize(text)
        issues: list[EditorialIssue] = []
        score = 80
        paras = paragraphs(text)
        sents = sentences(text)
        low = text.lower()

        has_context = bool(paras) or bool(sents)
        has_tension = bool(re.search(r"\b(but|however|problem|wrong|fail|constraint|instead)\b", low))
        has_insight = bool(re.search(r"\b(because|measured|learned|found|insight|trade-?off)\b", low))
        has_implication = bool(
            re.search(r"\b(so|therefore|next|should|recommend|what|implication)\b", low)
        ) or ("?" in text)

        if not has_context:
            issues.append(
                EditorialIssue(
                    code="STORY_ARC",
                    category="story",
                    severity=Severity.CRITICAL,
                    problem="No usable draft to review.",
                    why="Editorial review requires a complete post.",
                    suggestion="Provide the full draft before requesting desk review.",
                )
            )
            return CheckReport(name=self.name, score=0, issues=issues)

        missing = []
        if not has_tension:
            missing.append("tension")
        if not has_insight:
            missing.append("insight")
        if not has_implication:
            missing.append("implication")
        if missing:
            issues.append(
                EditorialIssue(
                    code="STORY_ARC",
                    category="story",
                    severity=Severity.MAJOR if len(missing) >= 2 else Severity.MINOR,
                    problem=f"Story arc incomplete — missing: {', '.join(missing)}.",
                    why="Economist/HBR-grade pieces move through conflict to implication.",
                    suggestion="Add the missing beat without inventing facts — use existing evidence.",
                )
            )
            score -= 12 * len(missing)

        if word_count(text) >= 70 and not has_transition_glue(text):
            issues.append(
                EditorialIssue(
                    code="LOGIC_LINKS",
                    category="flow",
                    severity=Severity.MAJOR,
                    problem="Logical flow is under-linked.",
                    why="Claims without causal/contrastive bridges feel arbitrary.",
                    suggestion="Insert because/however/instead between the two densest claims.",
                )
            )
            score -= 14

        practical = bool(
            re.search(r"\b(framework|checklist|metric|step|playbook|measure|constraint)\b", low)
        )
        if not practical and word_count(text) >= 80:
            issues.append(
                EditorialIssue(
                    code="PRACTICAL_USE",
                    category="practicality",
                    severity=Severity.MINOR,
                    problem="Limited practical usefulness signal.",
                    why="Readers should leave with a usable distinction or next step.",
                    suggestion="Surface one concrete action or decision rule already implied by the draft.",
                )
            )
            score -= 10
        else:
            score += 8

        if len(paras) >= 3:
            score += 6

        return CheckReport(name=self.name, score=clamp100(score), issues=issues)
