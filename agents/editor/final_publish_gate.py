"""Final publish gate — Approve / Minor / Major / Reject."""

from __future__ import annotations

from agents.editor.schemas import (
    EditorialIssue,
    EditorScore,
    PublishDecision,
    PublishGateResult,
    Severity,
)


class FinalPublishGate:
    name = "final_publish_gate"

    def decide(
        self,
        scores: EditorScore,
        issues: list[EditorialIssue],
    ) -> PublishGateResult:
        critical = [i for i in issues if i.severity == Severity.CRITICAL]
        major = [i for i in issues if i.severity == Severity.MAJOR]
        minor = [i for i in issues if i.severity == Severity.MINOR]
        rationale: list[str] = []
        blocking = [f"{i.code}: {i.problem}" for i in critical]

        overall = scores.overall

        if critical or scores.trust < 40 or scores.evidence < 35:
            decision = PublishDecision.REJECT
            rationale.append("Critical credibility/integrity issues block publication.")
            if critical:
                rationale.append(f"{len(critical)} critical issue(s) require removal or sourcing.")
        elif major and (overall < 75 or len(major) >= 2 or scores.clarity < 60):
            decision = PublishDecision.NEEDS_MAJOR_REVISION
            rationale.append("Major structural or clarity issues require substantial revision.")
            rationale.append(f"{len(major)} major issue(s); overall={overall}.")
        elif minor and overall < 88:
            decision = PublishDecision.NEEDS_MINOR_REVISION
            rationale.append("Publishable thesis, but minor editorial fixes needed.")
            rationale.append(f"{len(minor)} minor issue(s); overall={overall}.")
        elif overall >= 88 and not critical and len(major) == 0:
            decision = PublishDecision.APPROVE
            rationale.append("Meets Editor-in-Chief bar for clarity, trust, and usefulness.")
            if minor:
                rationale.append("Residual info-level notes may be ignored or polished later.")
        else:
            decision = PublishDecision.NEEDS_MINOR_REVISION
            rationale.append("Borderline score — request minor revision before publish.")

        # Always explain decision with score snapshot
        rationale.append(
            f"Score snapshot: clarity={scores.clarity}, trust={scores.trust}, "
            f"flow={scores.flow}, evidence={scores.evidence}, overall={overall}."
        )

        return PublishGateResult(
            decision=decision,
            rationale=rationale,
            blocking_issues=blocking,
            score_overall=overall,
        )
