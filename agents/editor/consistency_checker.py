"""Consistency checker — terminology, tone, tense, audience, contradictions."""

from __future__ import annotations

import re
from collections import defaultdict

from agents.editor._text import clamp100, normalize, sentences, tense_markers, words
from agents.editor.schemas import CheckReport, EditorialIssue, Severity


_TERM_ALIASES = (
    ("llm", "large language model"),
    ("ai", "artificial intelligence"),
    ("eval", "evaluation"),
    ("kpi", "metric"),
)


class ConsistencyChecker:
    name = "consistency_checker"

    def check(self, text: str) -> CheckReport:
        text = normalize(text)
        issues: list[EditorialIssue] = []
        score = 88

        # Terminology drift via alias pairs both present
        low = text.lower()
        for a, b in _TERM_ALIASES:
            if re.search(rf"\b{re.escape(a)}s?\b", low) and b in low:
                issues.append(
                    EditorialIssue(
                        code="TERMINOLOGY",
                        category="consistency",
                        severity=Severity.MINOR,
                        problem=f"Mixed terminology: '{a}' and '{b}' both appear.",
                        why="Readers infer carelessness when one concept has multiple labels.",
                        suggestion=f"Pick one term ('{a}' or '{b}') and use it consistently.",
                    )
                )
                score -= 8

        # Tone: brochure vs operator
        brochure = len(re.findall(r"\b(delighted|excited|thrilled|passionate|journey)\b", low))
        operator = len(re.findall(r"\b(measured|constraint|trade-?off|shipped|failed|because)\b", low))
        if brochure and operator:
            issues.append(
                EditorialIssue(
                    code="TONE_CONSISTENCY",
                    category="consistency",
                    severity=Severity.MAJOR,
                    problem="Tone shifts between promotional and operator voice.",
                    why="Mixed tone breaks the editorial contract with a single audience.",
                    suggestion="Commit to one voice — preferably concrete operator language.",
                )
            )
            score -= 15
        elif brochure >= 2:
            issues.append(
                EditorialIssue(
                    code="TONE_CONSISTENCY",
                    category="consistency",
                    severity=Severity.MINOR,
                    problem="Promotional tone dominates.",
                    why="Brochure adjectives reduce perceived seriousness.",
                    suggestion="Replace enthusiasm adjectives with observed constraints or results.",
                )
            )
            score -= 10

        markers = tense_markers(text)
        total = sum(markers.values()) or 1
        dominant = max(markers, key=markers.get)
        secondary = sorted(markers.items(), key=lambda kv: kv[1], reverse=True)
        if total >= 8 and len(secondary) > 1 and secondary[1][1] / total > 0.35 and secondary[0][0] != secondary[1][0]:
            if markers["future"] > 0 and markers["past"] > 0 and markers["present"] > 0:
                issues.append(
                    EditorialIssue(
                        code="TENSE_CONSISTENCY",
                        category="consistency",
                        severity=Severity.MINOR,
                        problem="Tense thrashing across past/present/future without clear framing.",
                        why=f"Dominant tense appears to be {dominant}, but others compete.",
                        suggestion="Anchor narrative tense; use others only for deliberate contrast.",
                    )
                )
                score -= 8

        # Soft contradiction cues
        sents = sentences(text)
        neg = [s for s in sents if re.search(r"\b(never|not|no longer|opposite)\b", s, re.I)]
        pos = [s for s in sents if re.search(r"\b(always|everyone|guaranteed)\b", s, re.I)]
        if neg and pos:
            issues.append(
                EditorialIssue(
                    code="CONTRADICTION",
                    category="consistency",
                    severity=Severity.MAJOR,
                    location=pos[0][:80],
                    problem="Absolute claims coexist with negations — possible contradiction.",
                    why="Unresolved contradictions erode trust and logic.",
                    suggestion="Qualify absolutes or reconcile the opposing statements explicitly.",
                )
            )
            score -= 18

        # Audience cues
        audiences = {
            "engineers": bool(re.search(r"\b(api|latency|eval|model|repo)\b", low)),
            "executives": bool(re.search(r"\b(roi|board|strategy|market)\b", low)),
            "founders": bool(re.search(r"\b(startup|founder|ship|runway)\b", low)),
        }
        active = [k for k, v in audiences.items() if v]
        if len(active) >= 3:
            issues.append(
                EditorialIssue(
                    code="AUDIENCE",
                    category="consistency",
                    severity=Severity.MINOR,
                    problem="Draft appears to address multiple audiences at once.",
                    why="Split audience weakens specificity and practical usefulness.",
                    suggestion="Choose one primary audience and cut cross-talk.",
                )
            )
            score -= 8

        return CheckReport(name=self.name, score=clamp100(score), issues=issues)
