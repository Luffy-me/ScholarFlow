"""AI evaluation tests for the Human Voice Agent."""

from __future__ import annotations

import pytest

from agents.humanizer import HumanizerAgent, HumanizerInput
from models.fake import FakeProvider
from shared.quality import scan_text


@pytest.mark.asyncio
async def test_humanizer_prefers_first_person_authentic_voice(user_memory: dict, bad_generic_post: str) -> None:
    provider = FakeProvider(
        scripted={
            "In today's rapidly evolving world": bad_generic_post,
        }
    )
    agent = HumanizerAgent(provider)
    result = await agent.run(HumanizerInput(text=bad_generic_post, user_memory=user_memory))
    scan = scan_text(result.text, user_memory)

    assert result.preferred_first_person is True
    assert scan.has_strong_first_person, "Humanizer should prefer first-person authentic writing"
    assert not scan.has_generic_ai, "Humanizer should remove generic AI / corporate phrasing"
    assert "rapidly evolving world" not in result.text.lower()


@pytest.mark.asyncio
async def test_humanizer_keeps_authentic_draft_human(provider: FakeProvider, user_memory: dict, good_post: str) -> None:
    agent = HumanizerAgent(provider)
    result = await agent.run(HumanizerInput(text=good_post, user_memory=user_memory))
    scan = scan_text(result.text, user_memory)
    assert scan.first_person_count >= 1
    assert not scan.has_generic_ai
