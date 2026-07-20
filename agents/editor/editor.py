"""Editor-in-Chief — critiques a draft; never writes or rewrites."""

from __future__ import annotations

from typing import Any

from agents.editor._text import clamp100, mean, normalize
from agents.editor.clarity_checker import ClarityChecker
from agents.editor.consistency_checker import ConsistencyChecker
from agents.editor.copy_editor import CopyEditor
from agents.editor.credibility_checker import CredibilityChecker
from agents.editor.final_publish_gate import FinalPublishGate
from agents.editor.redundancy_detector import RedundancyDetector
from agents.editor.schemas import (
    EditorialReport,
    EditorialResult,
    EditorialSuggestion,
    EditorScore,
    PublishDecision,
)
from agents.editor.story_reviewer import StoryReviewer
from agents.editor.tone_reviewer import ToneReviewer


class Editor:
    """Single editorial pass over an existing draft."""

    name = "editor"
    writes = False

    def __init__(self) -> None:
        self.story = StoryReviewer()
        self.clarity = ClarityChecker()
        self.consistency = ConsistencyChecker()
        self.credibility = CredibilityChecker()
        self.tone = ToneReviewer()
        self.redundancy = RedundancyDetector()
        self.copy = CopyEditor()
        self.gate = FinalPublishGate()

    def review(
        self,
        draft: str,
        *,
        evidence_refs: list[str] | None = None,
        user_memory: dict[str, Any] | None = None,
    ) -> EditorialResult:
        original = normalize(draft)
        story = self.story.check(original)
        clarity = self.clarity.check(original)
        consistency = self.consistency.check(original)
        credibility = self.credibility.check(
            original, evidence_refs=evidence_refs, user_memory=user_memory
        )
        tone = self.tone.check(original, user_memory=user_memory)
        redundancy = self.redundancy.check(original)
        copy = self.copy.check(original, user_memory=user_memory)

        issues = (
            list(story.issues)
            + list(clarity.issues)
            + list(consistency.issues)
            + list(credibility.issues)
            + list(tone.issues)
            + list(redundancy.issues)
            + list(copy.issues)
        )

        scores = self._score(
            story=story.score,
            clarity=clarity.score,
            consistency=consistency.score,
            credibility=credibility.score,
            tone=tone.score,
            redundancy=redundancy.score,
            copy=copy.score,
            text=original,
        )

        # Derived metrics
        linkedin = clamp100((clarity.score + tone.score) / 2)
        fatigue_issues = [i for i in issues if i.code == "READING_FATIGUE"]
        reading_fatigue = 30 if fatigue_issues else clamp100(100 - max(0, 90 - clarity.score))
        confidence = round(
            min(1.0, max(0.0, (scores.trust + scores.evidence) / 200 + (0.1 if evidence_refs else 0))),
            4,
        )

        suggestions = self._suggestions(issues)
        report = EditorialReport(
            summary=self._summary(scores, issues),
            scores=scores,
            story=story,
            clarity=clarity,
            consistency=consistency,
            credibility=credibility,
            tone=tone,
            redundancy=redundancy,
            copy_edit=copy,
            linkedin_friendliness=linkedin,
            reading_fatigue=reading_fatigue,
            confidence=confidence,
        )
        gate = self.gate.decide(scores, issues)

        # Editor never rewrites: approved_draft only when Approve, else empty
        approved = original if gate.decision == PublishDecision.APPROVE else ""

        return EditorialResult(
            original_draft=original,
            editorial_report=report,
            issues=issues,
            suggestions=suggestions,
            approved_draft=approved,
            publish_decision=gate.decision,
            gate=gate,
            meta={
                "writes": False,
                "rewrites": False,
                "invents_facts": False,
                "changes_verified_evidence": False,
                "role": "editor_in_chief",
            },
        )

    def _score(
        self,
        *,
        story: int,
        clarity: int,
        consistency: int,
        credibility: int,
        tone: int,
        redundancy: int,
        copy: int,
        text: str,
    ) -> EditorScore:
        novelty = clamp100(tone * 0.6 + (10 if "instead" in text.lower() or "overlooked" in text.lower() else 0) + 20)
        practicality = clamp100(story if "framework" in text.lower() or "metric" in text.lower() or "constraint" in text.lower() else story - 10)
        authority = clamp100((credibility + tone) / 2)
        originality = clamp100(tone if "synergy" not in text.lower() else tone - 25)
        readability = clamp100((clarity + copy) / 2)
        flow = clamp100((story + clarity + consistency) / 3)
        trust = clamp100((credibility + consistency) / 2)
        evidence = credibility
        dims = {
            "clarity": clarity,
            "trust": trust,
            "flow": flow,
            "novelty": novelty,
            "evidence": evidence,
            "readability": readability,
            "authority": authority,
            "originality": originality,
            "practicality": clamp100(practicality),
        }
        overall = clamp100(mean([float(v) for v in dims.values()]))
        return EditorScore(
            clarity=clarity,
            trust=trust,
            flow=flow,
            novelty=novelty,
            evidence=evidence,
            readability=readability,
            authority=authority,
            originality=originality,
            practicality=clamp100(practicality),
            overall=overall,
            dimensions=dims,
        )

    def _suggestions(self, issues: list) -> list[EditorialSuggestion]:
        sev_rank = {"critical": 1, "major": 2, "minor": 3, "info": 4}
        out: list[EditorialSuggestion] = []
        seen: set[str] = set()
        for issue in sorted(issues, key=lambda i: sev_rank.get(str(i.severity.value), 5)):
            key = f"{issue.code}:{issue.suggestion}"
            if key in seen or not issue.suggestion:
                continue
            seen.add(key)
            out.append(
                EditorialSuggestion(
                    category=issue.category,
                    suggestion=issue.suggestion,
                    why=issue.why,
                    priority=sev_rank.get(str(issue.severity.value), 3),
                )
            )
        return out[:20]

    def _summary(self, scores: EditorScore, issues: list) -> str:
        critical = sum(1 for i in issues if i.severity.value == "critical")
        major = sum(1 for i in issues if i.severity.value == "major")
        return (
            f"Editorial desk score {scores.overall}/100 with {critical} critical and "
            f"{major} major issue(s). Trust={scores.trust}, clarity={scores.clarity}, "
            f"evidence={scores.evidence}."
        )
