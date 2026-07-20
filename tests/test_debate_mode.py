"""Debate Mode tests — Qwen write, DeepSeek critique/score."""

from __future__ import annotations

import pytest

from agents.debate import DebateMode
from agents.insight_engine import generate_insight
from models.router import RouterCallRecorder, family_for_stage, provider_for_stage
from shared.quality import scan_text


@pytest.mark.asyncio
async def test_generic_posts_are_rejected_by_debate() -> None:
    recorder = RouterCallRecorder()
    debate = DebateMode(
        writer_provider=provider_for_stage("writer", fake=True, recorder=recorder),
        critic_provider=provider_for_stage("debate_critic", fake=True, recorder=recorder),
        rewrite_provider=provider_for_stage("debate_rewrite", fake=True, recorder=recorder),
    )
    generic = (
        "In today's rapidly evolving world, AI is revolutionizing industries. "
        "It is important to note that seamless integration unlocks potential."
    )
    result = await debate.run(
        topic="AI",
        content_mode="founder",
        format="short",
        user_memory={},
        initial_draft=generic,
    )
    assert result.review.rejected is True or result.generic_rejected is True
    assert result.final_score.accepted is False or result.final_score.ai_pattern_risk >= 70
    assert family_for_stage("debate_critic") == "deepseek"
    assert family_for_stage("debate_rewrite") == "qwen"
    assert any(c["family"] == "deepseek" for c in recorder.calls)
    assert any(c["family"] == "qwen" for c in recorder.calls)


@pytest.mark.asyncio
async def test_insight_quality_improves_with_deepseek_reasoning() -> None:
    weak = await generate_insight(
        None,
        topic="AI",
        verified_experiences=[],
    )
    deepseek = provider_for_stage("insight_engine", fake=True)
    strong = await generate_insight(
        deepseek,
        topic="local LLM evaluation loops",
        verified_experiences=[
            "I tested Qwen locally on my MacBook and noticed workflow design mattered more than model size"
        ],
        research={"key_findings": ["Evaluation loops matter more than model size"]},
    )
    assert strong.quality.strength_score > weak.quality.strength_score
    assert strong.insight.originality_score >= weak.insight.originality_score
    assert strong.meta.get("reasoning_family") == "deepseek"
    assert strong.insight.hidden_pattern
    assert strong.insight.contrarian_view


@pytest.mark.asyncio
async def test_debate_rewrite_reduces_generic_patterns() -> None:
    debate = DebateMode(
        writer_provider=provider_for_stage("writer", fake=True),
        critic_provider=provider_for_stage("debate_critic", fake=True),
        rewrite_provider=provider_for_stage("debate_rewrite", fake=True),
    )
    generic = (
        "In today's rapidly evolving world, artificial intelligence is revolutionizing "
        "the technology landscape."
    )
    before = scan_text(generic, {})
    assert before.has_generic_ai

    result = await debate.run(
        topic="evaluation loops",
        content_mode="engineer",
        format="short",
        user_memory={"projects": ["RAG chatbot"], "experiences": [], "verified_experiences": []},
        initial_draft=generic,
    )
    after = scan_text(result.draft_v2, {})
    # Fake humanizer/deterministic path should move away from pure generic filler.
    assert result.draft_v2.strip()
    assert (not after.has_generic_ai) or result.review.improvements
