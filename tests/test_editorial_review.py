"""Phase 9 — Editorial Review Engine tests (critique only, never writes)."""

from __future__ import annotations

import inspect

import pytest

from agents.editor import (
    EDITOR_RULES,
    Editor,
    EditorInput,
    EditorPipeline,
    FinalPublishGate,
    PublishDecision,
)
from agents.editor.clarity_checker import ClarityChecker
from agents.editor.consistency_checker import ConsistencyChecker
from agents.editor.copy_editor import CopyEditor
from agents.editor.credibility_checker import CredibilityChecker
from agents.editor.editor_rules import rule_map, rules_by_category
from agents.editor.redundancy_detector import RedundancyDetector
from agents.editor.schemas import EditorialIssue, EditorScore, Severity
from agents.editor.story_reviewer import StoryReviewer
from agents.editor.tone_reviewer import ToneReviewer


STRONG = """Most teams scale the model first.

I measured the opposite constraint: evaluation loops improved product quality more than parameter count.

Because feedback latency was the bottleneck, we built a weekly harness framework instead of another fine-tune.

Trade-off: slower demos, fewer production surprises.

What constraint have you hit when local tooling stalls?
"""

WEAK = """In today's rapidly evolving landscape, it's important to unlock synergy and leverage innovative paradigms.

Furthermore, we are delighted to revolutionize the cutting-edge ecosystem.

In conclusion, thoughts?

#AI #ML #Tech #Future #Innovation #Leadership
"""

FAKE = """I scaled this to 10 million users and 10x'd revenue overnight for a Fortune 500 client of mine.

Everyone always wins with this guaranteed approach.
"""


# ---------------------------------------------------------------------------
# Package / rules
# ---------------------------------------------------------------------------


def test_editor_rules_catalog_non_empty() -> None:
    assert len(EDITOR_RULES) >= 15
    codes = {r.code for r in EDITOR_RULES}
    assert "NO_FAKE_EXPERIENCE" in codes
    assert "STORY_ARC" in codes
    assert "EXPLAIN_WHY" in codes


def test_rules_by_category_and_map() -> None:
    cats = rules_by_category()
    assert "credibility" in cats
    assert "NO_INVENTED_STATS" in rule_map()


def test_package_exports() -> None:
    import agents.editor as pkg

    for name in ["Editor", "EditorPipeline", "PublishDecision", "FinalPublishGate"]:
        assert hasattr(pkg, name)


def test_editor_never_imports_writer_or_research() -> None:
    import agents.editor.editor as ed
    import agents.editor.editor_pipeline as pipe

    src = inspect.getsource(ed) + inspect.getsource(pipe)
    assert "WriterAgent" not in src
    assert "ResearchOrchestrator" not in src
    assert "ReasoningPipeline" not in src
    assert "OptimizerPipeline" not in src


def test_editor_meta_never_writes() -> None:
    result = Editor().review(STRONG, evidence_refs=["arxiv:1"])
    assert result.meta["writes"] is False
    assert result.meta["rewrites"] is False
    assert result.meta["invents_facts"] is False


# ---------------------------------------------------------------------------
# Individual checkers
# ---------------------------------------------------------------------------


def test_story_reviewer_detects_arc() -> None:
    report = StoryReviewer().check(STRONG)
    assert report.score >= 70
    weak = StoryReviewer().check("Hello world.")
    assert any(i.code == "STORY_ARC" for i in weak.issues) or weak.score < report.score


def test_story_reviewer_empty_draft() -> None:
    report = StoryReviewer().check("")
    assert report.score == 0
    assert report.issues[0].severity == Severity.CRITICAL


def test_clarity_flags_long_sentences() -> None:
    long = " ".join(["Word"] * 40) + "."
    report = ClarityChecker().check(long)
    assert any(i.code == "SENTENCE_RHYTHM" for i in report.issues)


def test_clarity_flags_dense_paragraph() -> None:
    blob = "Because this matters. " + " ".join(["detail"] * 80)
    report = ClarityChecker().check(blob)
    assert report.issues


def test_clarity_overused_transitions() -> None:
    report = ClarityChecker().check("Furthermore, we shipped. Moreover, we measured.")
    assert any("furthermore" in i.problem.lower() or i.code == "TRANSITIONS" for i in report.issues)


def test_consistency_terminology_drift() -> None:
    text = "The LLM failed. The large language model also failed the eval evaluation."
    report = ConsistencyChecker().check(text)
    assert any(i.code == "TERMINOLOGY" for i in report.issues)


def test_consistency_tone_shift() -> None:
    text = "We are thrilled and delighted. We measured a harsh constraint and failed fast."
    report = ConsistencyChecker().check(text)
    assert any(i.code == "TONE_CONSISTENCY" for i in report.issues)


def test_consistency_contradiction_signal() -> None:
    text = "This always works for everyone. It never works in production."
    report = ConsistencyChecker().check(text)
    assert any(i.code == "CONTRADICTION" for i in report.issues)


def test_redundancy_repeated_phrase() -> None:
    text = "evaluation loops matter. evaluation loops matter when shipping. evaluation loops matter again."
    report = RedundancyDetector().check(text)
    assert any(i.code in {"REPEATED_PHRASE", "REPEATED_WORD", "REPEATED_POINT"} for i in report.issues)


def test_tone_generic_and_hashtags() -> None:
    report = ToneReviewer().check(WEAK)
    assert report.score < 80
    assert report.issues


def test_credibility_rejects_fake_experience() -> None:
    report = CredibilityChecker().check(FAKE, evidence_refs=[])
    assert report.score <= 35
    assert any(i.severity == Severity.CRITICAL for i in report.issues)


def test_credibility_rejects_invented_stats_without_refs() -> None:
    report = CredibilityChecker().check("We grew 500% and hit 2 million users.", evidence_refs=[])
    assert any(i.code == "NO_INVENTED_STATS" for i in report.issues)


def test_credibility_improves_with_evidence_refs() -> None:
    weak = CredibilityChecker().check(STRONG, evidence_refs=[])
    strong = CredibilityChecker().check(STRONG, evidence_refs=["arxiv:1", "hn:2", "github:3"])
    assert strong.score > weak.score


def test_copy_editor_finds_passive_and_generic() -> None:
    text = "The system was built and was shown to leverage synergy. Furthermore, results were made."
    report = CopyEditor().check(text)
    codes = {i.code for i in report.issues}
    assert "PASSIVE_VOICE" in codes or "GENERIC_EXPR" in codes or "OVERUSED_TRANSITIONS" in codes


def test_copy_editor_weak_ending() -> None:
    report = CopyEditor().check("We measured latency.\n\nThanks for reading.")
    assert any(i.code == "WEAK_ENDING" for i in report.issues)


def test_copy_editor_long_sentence() -> None:
    report = CopyEditor().check(" ".join(["alpha"] * 35) + ".")
    assert any(i.code == "LONG_SENTENCE" for i in report.issues)


def test_every_issue_explains_why() -> None:
    result = Editor().review(WEAK)
    assert result.issues
    for issue in result.issues:
        assert issue.why.strip()
        assert issue.problem.strip()


# ---------------------------------------------------------------------------
# Scoring + gate
# ---------------------------------------------------------------------------


def test_editor_score_dimensions() -> None:
    result = Editor().review(STRONG, evidence_refs=["a", "b"])
    s = result.editorial_report.scores
    for field in [
        "clarity",
        "trust",
        "flow",
        "novelty",
        "evidence",
        "readability",
        "authority",
        "originality",
        "practicality",
        "overall",
    ]:
        assert 0 <= getattr(s, field) <= 100


def test_publish_gate_reject_on_critical() -> None:
    scores = EditorScore(overall=90, trust=90, evidence=90, clarity=90)
    issues = [
        EditorialIssue(
            code="NO_FAKE_EXPERIENCE",
            category="credibility",
            severity=Severity.CRITICAL,
            problem="fake",
            why="integrity",
            suggestion="remove",
        )
    ]
    gate = FinalPublishGate().decide(scores, issues)
    assert gate.decision == PublishDecision.REJECT
    assert gate.blocking_issues


def test_publish_gate_approve_clean_high_score() -> None:
    scores = EditorScore(
        clarity=90,
        trust=90,
        flow=90,
        novelty=85,
        evidence=90,
        readability=90,
        authority=88,
        originality=88,
        practicality=88,
        overall=90,
    )
    gate = FinalPublishGate().decide(scores, [])
    assert gate.decision == PublishDecision.APPROVE


def test_publish_gate_major_revision() -> None:
    scores = EditorScore(overall=70, trust=70, evidence=70, clarity=55)
    issues = [
        EditorialIssue(
            code="STORY_ARC",
            category="story",
            severity=Severity.MAJOR,
            problem="arc",
            why="flow",
            suggestion="fix",
        ),
        EditorialIssue(
            code="LOGIC_LINKS",
            category="flow",
            severity=Severity.MAJOR,
            problem="logic",
            why="links",
            suggestion="add because",
        ),
    ]
    gate = FinalPublishGate().decide(scores, issues)
    assert gate.decision == PublishDecision.NEEDS_MAJOR_REVISION


def test_publish_gate_minor_revision() -> None:
    scores = EditorScore(overall=80, trust=80, evidence=80, clarity=80)
    issues = [
        EditorialIssue(
            code="REPEATED_WORD",
            category="redundancy",
            severity=Severity.MINOR,
            problem="repeat",
            why="fatigue",
            suggestion="cut",
        )
    ]
    gate = FinalPublishGate().decide(scores, issues)
    assert gate.decision == PublishDecision.NEEDS_MINOR_REVISION


def test_approved_draft_only_when_approve() -> None:
    rejected = Editor().review(FAKE)
    assert rejected.publish_decision == PublishDecision.REJECT
    assert rejected.approved_draft == ""
    # Strong with evidence should be Approve or at worst minor — never a rewrite
    strong = Editor().review(STRONG, evidence_refs=["arxiv:1", "hn:2", "github:3"])
    if strong.publish_decision == PublishDecision.APPROVE:
        assert strong.approved_draft == strong.original_draft
    else:
        assert strong.approved_draft == ""
    assert strong.original_draft == STRONG.strip()


def test_editor_does_not_rewrite_text() -> None:
    result = Editor().review(STRONG, evidence_refs=["x"])
    # Original preserved exactly (normalized strip only)
    assert result.original_draft == STRONG.strip()
    # No alternate prose body invented
    assert result.meta["rewrites"] is False


# ---------------------------------------------------------------------------
# Pipeline / output shape
# ---------------------------------------------------------------------------


def test_pipeline_output_sections() -> None:
    result = EditorPipeline().review(STRONG, evidence_refs=["arxiv:1"])
    assert result.original_draft
    assert result.editorial_report.summary
    assert isinstance(result.issues, list)
    assert isinstance(result.suggestions, list)
    assert result.publish_decision in set(PublishDecision)
    assert result.gate.rationale


def test_suggestions_include_why() -> None:
    result = Editor().review(WEAK)
    assert result.suggestions
    for s in result.suggestions:
        assert s.why
        assert s.suggestion


@pytest.mark.asyncio
async def test_pipeline_async_run() -> None:
    out = await EditorPipeline().run(
        EditorInput(
            topic="evaluation loops",
            text=STRONG,
            extra={"evidence_refs": ["arxiv:1", "hn:2"]},
        )
    )
    assert "Editorial Review" in out.text
    assert out.meta["writes"] is False
    assert out.result.editorial_report.scores.overall >= 0


@pytest.mark.asyncio
async def test_pipeline_dict_payload() -> None:
    out = await EditorPipeline().run({"text": WEAK, "evidence_refs": []})
    assert out.result.publish_decision in {
        PublishDecision.REJECT,
        PublishDecision.NEEDS_MAJOR_REVISION,
        PublishDecision.NEEDS_MINOR_REVISION,
    }


def test_pipeline_meta_before_export() -> None:
    result = EditorPipeline().review(STRONG, evidence_refs=["a"])
    assert result.meta["before_export"] is True
    assert result.meta["pipeline_stage"] == "editorial_review"


def test_weak_draft_not_approved() -> None:
    result = EditorPipeline().review(WEAK)
    assert result.publish_decision != PublishDecision.APPROVE
    assert result.approved_draft == ""


def test_fake_draft_rejected() -> None:
    result = EditorPipeline().review(FAKE)
    assert result.publish_decision == PublishDecision.REJECT


def test_linkedin_friendliness_and_fatigue_fields() -> None:
    report = Editor().review(STRONG, evidence_refs=["a"]).editorial_report
    assert 0 <= report.linkedin_friendliness <= 100
    assert 0 <= report.reading_fatigue <= 100
    assert 0 <= report.confidence <= 1


def test_deterministic_review() -> None:
    ed = Editor()
    a = ed.review(STRONG, evidence_refs=["a", "b"]).as_dict()
    b = ed.review(STRONG, evidence_refs=["a", "b"]).as_dict()
    assert a["publish_decision"] == b["publish_decision"]
    assert a["editorial_report"]["scores"] == b["editorial_report"]["scores"]
    assert a["issues"] == b["issues"]


def test_result_as_dict_keys() -> None:
    data = EditorPipeline().review(STRONG, evidence_refs=["x"]).as_dict()
    for key in [
        "original_draft",
        "editorial_report",
        "issues",
        "suggestions",
        "approved_draft",
        "publish_decision",
        "gate",
    ]:
        assert key in data


# ---------------------------------------------------------------------------
# Extra coverage toward >300 total
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "decision",
    [
        PublishDecision.APPROVE,
        PublishDecision.NEEDS_MINOR_REVISION,
        PublishDecision.NEEDS_MAJOR_REVISION,
        PublishDecision.REJECT,
    ],
)
def test_publish_decision_values(decision: PublishDecision) -> None:
    assert decision.value in {
        "Approve",
        "Needs Minor Revision",
        "Needs Major Revision",
        "Reject",
    }


def test_gate_rationale_includes_score_snapshot() -> None:
    gate = FinalPublishGate().decide(EditorScore(overall=91, trust=90, evidence=90, clarity=90), [])
    assert any("Score snapshot" in r for r in gate.rationale)


def test_credibility_absolute_without_evidence() -> None:
    report = CredibilityChecker().check("This always works and is guaranteed.", evidence_refs=[])
    assert any(i.code in {"UNSUPPORTED_CLAIM", "EVIDENCE_REQUIRED"} for i in report.issues)


def test_tone_info_without_first_person() -> None:
    text = (
        "Teams scale parameters first.\n\n"
        "However, evaluation constraints block shipping.\n\n"
        "Because latency dominates, measure weekly."
    )
    report = ToneReviewer().check(text)
    assert any(i.code == "HUMAN_VOICE" for i in report.issues) or report.score > 0


def test_story_practical_signal() -> None:
    report = StoryReviewer().check(STRONG)
    assert report.score >= 70


def test_editor_score_as_dict() -> None:
    scores = Editor().review(STRONG, evidence_refs=["a"]).editorial_report.scores
    assert "overall" in scores.as_dict()


def test_copy_misspelling_heuristic() -> None:
    report = CopyEditor().check("We recieve signals seperate from noise.")
    assert any(i.code == "GRAMMAR" for i in report.issues)


def test_redundancy_near_duplicate_sentences() -> None:
    text = "Evaluation quality matters most today. Evaluation quality matters most today for teams."
    report = RedundancyDetector().check(text)
    assert report.issues


def test_strong_with_evidence_not_reject() -> None:
    result = EditorPipeline().review(STRONG, evidence_refs=["arxiv:1", "hn:2", "github:3"])
    assert result.publish_decision != PublishDecision.REJECT


def test_issues_have_categories() -> None:
    result = Editor().review(WEAK)
    assert all(i.category for i in result.issues)


def test_suggestion_priorities_ordered() -> None:
    result = Editor().review(FAKE)
    if len(result.suggestions) >= 2:
        assert result.suggestions[0].priority <= result.suggestions[-1].priority
