"""AI evaluation tests for the Writer Agent."""

from __future__ import annotations

import pytest

from agents.writer import WriterAgent, WriterInput
from models.fake import FakeProvider
from shared.quality import scan_text


@pytest.mark.asyncio
async def test_writer_prefers_first_person_authentic_writing(provider: FakeProvider, user_memory: dict) -> None:
    agent = WriterAgent(provider)
    result = await agent.run(
        WriterInput(
            topic="local AI evaluation loops",
            content_mode="founder",
            format="short",
            user_memory=user_memory,
        )
    )
    scan = scan_text(result.text, user_memory)
    assert scan.has_strong_first_person, "Writer should prefer first-person authentic writing"
    assert not scan.has_generic_ai, "Writer output should not contain banned generic AI phrases"
    assert "I " in result.text or "I've" in result.text or "my " in result.text.lower()


@pytest.mark.asyncio
async def test_writer_rejects_fake_personal_experiences(user_memory: dict) -> None:
    # Script a provider response that invents ungrounded scale claims.
    provider = FakeProvider(
        scripted={
            "Write a LinkedIn post draft now": (
                "I built a million-user product and tested this with thousands of customers. "
                "Artificial intelligence is revolutionizing everything."
            )
        }
    )
    agent = WriterAgent(provider)
    result = await agent.run(
        WriterInput(
            topic="growth",
            content_mode="founder",
            format="short",
            user_memory=user_memory,
        )
    )
    lowered = result.text.lower()
    assert "million-user" not in lowered
    assert "thousands of customers" not in lowered
    scan = scan_text(result.text, user_memory)
    assert not scan.has_fake_experience
    # Either stripped/rejected or replaced with deterministic authentic draft.
    assert result.rejected_fake_experiences or scan.has_strong_first_person


@pytest.mark.asyncio
async def test_writer_does_not_invent_experiences_outside_memory(provider: FakeProvider) -> None:
    empty_memory = {
        "background": [],
        "skills": [],
        "projects": [],
        "experiences": [],
        "style": {"first_person": True, "tone": "neutral", "sentence_style": "short"},
    }
    agent = WriterAgent(provider)
    result = await agent.run(
        WriterInput(
            topic="career advice",
            content_mode="career_journey",
            format="short",
            user_memory=empty_memory,
        )
    )
    scan = scan_text(result.text, empty_memory)
    assert not scan.has_fake_experience
    assert "million-user" not in result.text.lower()
