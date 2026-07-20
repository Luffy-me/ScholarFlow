"""AI evaluation tests for the Critic Agent."""

from __future__ import annotations

import pytest

from agents.critic import CriticAgent, CriticInput
from models.fake import FakeProvider
from shared.quality import scan_text


@pytest.mark.asyncio
async def test_critic_detects_generic_ai_writing(
    provider: FakeProvider, user_memory: dict, bad_generic_post: str
) -> None:
    agent = CriticAgent(provider)
    result = await agent.run(CriticInput(text=bad_generic_post, user_memory=user_memory))

    assert any("Generic AI writing detected" in issue for issue in result.issues)
    assert result.scores.ai_pattern_score >= 70
    assert result.scores.human_quality <= 40


@pytest.mark.asyncio
async def test_critic_rejects_fake_personal_experiences(
    provider: FakeProvider, user_memory: dict, bad_fake_experience_post: str
) -> None:
    agent = CriticAgent(provider)
    result = await agent.run(CriticInput(text=bad_fake_experience_post, user_memory=user_memory))

    assert any("Fake personal experience" in issue for issue in result.issues) or any(
        "Ungrounded experience" in issue for issue in result.issues
    )
    assert result.scores.evidence_quality <= 30


@pytest.mark.asyncio
async def test_critic_identifies_weak_hooks(provider: FakeProvider, user_memory: dict) -> None:
    weak = (
        "Artificial intelligence is transforming the workplace.\n\n"
        "Here are some tips for leaders."
    )
    scan = scan_text(weak, user_memory)
    assert scan.has_weak_hook

    agent = CriticAgent(provider)
    result = await agent.run(CriticInput(text=weak, user_memory=user_memory))
    assert any("Weak hook" in issue for issue in result.issues)
    assert result.scores.engagement_probability <= 40


@pytest.mark.asyncio
async def test_critic_scores_authentic_first_person_higher(
    provider: FakeProvider, user_memory: dict, good_post: str
) -> None:
    agent = CriticAgent(provider)
    result = await agent.run(CriticInput(text=good_post, user_memory=user_memory))
    assert result.scores.human_quality >= 65
    assert result.scores.ai_pattern_score < 70
