"""Quality scoring and rewrite loop tests."""

from __future__ import annotations

import pytest

from agents.quality import QualityScorer, RewriteLoop


def test_quality_score_shape_and_generic_penalty() -> None:
    scorer = QualityScorer()
    generic = scorer.score(
        "In today's rapidly evolving world, AI is revolutionizing industries.",
        safe=True,
    )
    specific = scorer.score(
        "I tested Qwen locally on my MacBook and noticed the evaluation loop mattered more than model size.\n\nWhat would you measure first?",
        safe=True,
    )
    for key in (
        "truth",
        "specificity",
        "clarity",
        "human_voice",
        "originality",
        "novelty",
        "reader_value",
        "discussion_potential",
        "engagement",
        "technical_accuracy",
        "overall",
    ):
        assert key in generic.as_dict()
    assert specific.overall > generic.overall
    assert generic.details.get("generic_ai") is True


@pytest.mark.asyncio
async def test_rewrite_loop_max_three_iterations() -> None:
    calls = {"n": 0}

    async def rewrite(text: str, improvements: list[str]) -> str:
        calls["n"] += 1
        # Stay mediocre so loop hits max iterations.
        return text + f"\nIteration note {calls['n']}."

    loop = RewriteLoop(threshold=90, max_iterations=3)
    result = await loop.run(
        "In today's rapidly evolving world, AI is revolutionizing industries.",
        rewrite=rewrite,
        safe=True,
    )
    assert result["iterations"] == 3
    assert result["reached_threshold"] is False
    assert len(result["history"]) == 4  # initial + 3


@pytest.mark.asyncio
async def test_rewrite_loop_stops_when_threshold_met() -> None:
    async def rewrite(text: str, improvements: list[str]) -> str:
        return (
            "I tested Qwen locally on my MacBook and noticed workflow design mattered more than model size.\n\n"
            "My takeaway: write failing tests for generic phrasing before chasing parameters.\n\n"
            "What constraint shapes your evaluation loop?"
        )

    loop = RewriteLoop(threshold=50, max_iterations=3)
    result = await loop.run(
        "In today's rapidly evolving world, AI is revolutionizing industries.",
        rewrite=rewrite,
        safe=True,
    )
    assert result["iterations"] <= 3
    assert result["score"]["overall"] >= 50
