"""Insight Engine tests."""

from __future__ import annotations

import pytest

from agents.insight_engine import (
    Insight,
    InsightEngineAgent,
    InsightEngineInput,
    evaluate_insight_quality,
    generate_insight,
)
from models.fake import FakeProvider


@pytest.mark.asyncio
async def test_generic_ai_topic_produces_weak_insight() -> None:
    result = await generate_insight(
        None,
        topic="AI",
        content_mode="founder",
        verified_experiences=[],
        research={},
        trends={},
    )
    assert result.quality.is_weak is True
    assert result.quality.strength_score < 55
    assert "generic_observation" in result.quality.flags or "motivational_statement" in result.quality.flags
    assert result.insight.originality_score < 40


@pytest.mark.asyncio
async def test_specific_personal_experience_produces_stronger_insight() -> None:
    weak = await generate_insight(
        None,
        topic="AI",
        verified_experiences=[],
    )
    strong = await generate_insight(
        None,
        topic="local LLM evaluation loops",
        verified_experiences=[
            "I tested Qwen locally on my MacBook and noticed workflow design mattered more than model size"
        ],
        research={
            "key_findings": ["Evaluation loops matter more than model size"],
        },
    )
    assert strong.quality.strength_score > weak.quality.strength_score
    assert strong.quality.is_strong is True
    assert strong.quality.is_weak is False
    blob = " ".join(str(v) for v in strong.insight.as_dict().values()).lower()
    assert "evaluation" in blob or "qwen" in blob or "workflow" in blob
    assert strong.insight.originality_score > weak.insight.originality_score


@pytest.mark.asyncio
async def test_common_belief_vs_new_perspective_generated(provider: FakeProvider) -> None:
    result = await generate_insight(
        provider,
        topic="RAG retrieval quality",
        audience="engineers",
        verified_experiences=["Built and iterated on local RAG prototypes"],
        research={"key_findings": ["Tighter questions beat longer context"]},
    )
    insight = result.insight
    assert insight.common_belief.strip()
    assert insight.contrarian_view.strip()
    assert insight.common_belief.strip().lower() != insight.contrarian_view.strip().lower()
    assert result.quality.has_belief_contrast is True
    assert insight.hidden_pattern.strip()


@pytest.mark.asyncio
async def test_reader_takeaway_is_actionable(provider: FakeProvider) -> None:
    result = await InsightEngineAgent(provider).run(
        InsightEngineInput(
            topic="content evaluation for local models",
            content_mode="engineer",
            extra={
                "audience": "builders",
                "research": {"key_findings": ["Failing tests sharpen drafts"]},
                "trends": {"why_it_matters": "Generic AI posts are saturated"},
                "verified_experiences": [
                    "Compared local LLM workflows with cloud APIs for content drafting"
                ],
            },
        )
    )
    takeaway = result.insight.reader_takeaway
    assert takeaway.strip()
    assert result.quality.takeaway_actionable is True
    assert any(
        verb in takeaway.lower()
        for verb in ("try", "test", "write", "measure", "compare", "cut", "ask", "run")
    )


def test_evaluate_insight_quality_detects_belief_contrast_and_actionable_takeaway() -> None:
    weak = Insight(
        hidden_pattern="AI is changing everything",
        why_it_matters="The future of work",
        common_belief="AI matters",
        contrarian_view="AI matters a lot",
        supporting_reasoning="",
        reader_takeaway="Stay inspired",
        originality_score=10,
    )
    strong = Insight(
        hidden_pattern="The surprising bottleneck is the evaluation loop, not model size.",
        why_it_matters="Teams upgrade models before measuring failure modes.",
        common_belief="Bigger models automatically produce better drafts.",
        contrarian_view="Failing tests and tighter criteria beat model swaps.",
        supporting_reasoning="Local Qwen evaluation experiments",
        reader_takeaway="Write one failing test for generic phrasing, then compare two models.",
        originality_score=80,
    )
    weak_q = evaluate_insight_quality(weak, topic="AI")
    strong_q = evaluate_insight_quality(strong, topic="local models")
    assert weak_q.is_weak
    assert strong_q.has_belief_contrast
    assert strong_q.takeaway_actionable
    assert strong_q.strength_score > weak_q.strength_score
