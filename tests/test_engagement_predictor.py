"""AI evaluation tests for the Engagement Predictor Agent."""

from __future__ import annotations

import pytest

from agents.engagement_predictor import EngagementPredictorAgent, EngagementPredictorInput
from models.fake import FakeProvider


REQUIRED_SCORE_FIELDS = {
    "overall_score",
    "hook_score",
    "originality_score",
    "specificity_score",
    "discussion_score",
    "ai_pattern_score",
    "problems",
    "improvements",
}


@pytest.mark.asyncio
async def test_engagement_scoring_returns_structured_output(
    provider: FakeProvider, user_memory: dict, good_post: str
) -> None:
    agent = EngagementPredictorAgent(provider)
    result = await agent.run(EngagementPredictorInput(text=good_post, user_memory=user_memory))
    payload = result.scores.model_dump()

    assert REQUIRED_SCORE_FIELDS.issubset(payload.keys())
    for key in (
        "overall_score",
        "hook_score",
        "originality_score",
        "specificity_score",
        "discussion_score",
        "ai_pattern_score",
    ):
        assert isinstance(payload[key], int)
        assert 0 <= payload[key] <= 100
    assert isinstance(payload["problems"], list)
    assert isinstance(payload["improvements"], list)


@pytest.mark.asyncio
async def test_engagement_predictor_detects_generic_ai_writing(
    provider: FakeProvider, user_memory: dict, bad_generic_post: str
) -> None:
    agent = EngagementPredictorAgent(provider)
    result = await agent.run(EngagementPredictorInput(text=bad_generic_post, user_memory=user_memory))

    assert result.scores.ai_pattern_score >= 70
    assert any("Generic AI writing detected" in p for p in result.scores.problems)
    assert result.scores.overall_score <= 50


@pytest.mark.asyncio
async def test_engagement_predictor_identifies_weak_hooks(
    provider: FakeProvider, user_memory: dict
) -> None:
    weak = "In today's world, success is a journey.\n\nMany people think hustle is enough."
    agent = EngagementPredictorAgent(provider)
    result = await agent.run(EngagementPredictorInput(text=weak, user_memory=user_memory))

    assert result.scores.hook_score <= 40
    assert any("Weak hook" in p for p in result.scores.problems)
    assert any(isinstance(item, str) and item for item in result.scores.improvements)
