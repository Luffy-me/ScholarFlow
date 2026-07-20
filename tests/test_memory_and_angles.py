"""Tests for verified experience memory and angle finder."""

from __future__ import annotations

import pytest

from agents.angle_finder import AngleFinderAgent, AngleFinderInput
from agents.grounding import check_claims
from agents.memory_builder import (
    approve_experience,
    approved_experience_texts,
    is_experience_approved,
    list_pending_experiences,
    list_verified_experiences,
    normalize_memory,
    propose_experience,
)
from models.fake import FakeProvider


def test_approved_experiences_reused(user_memory: dict) -> None:
    memory = normalize_memory(user_memory)
    approved = approved_experience_texts(memory)
    assert any("RAG chatbot" in item for item in approved)
    assert is_experience_approved("Built a RAG chatbot", memory)
    # Writer/grounding path can reuse approved project facts.
    text = "I built a RAG chatbot and kept making the same mistake."
    result = check_claims(text, memory)
    assert result.safe is True


def test_unapproved_experiences_rejected(user_memory: dict) -> None:
    memory = normalize_memory(user_memory)
    memory, pending = propose_experience(
        "I closed a $2M enterprise deal with Acme Corp",
        category="achievement",
        memory=memory,
    )
    assert pending["approved"] is False
    assert pending["reusable"] is False
    assert not is_experience_approved("I closed a $2M enterprise deal with Acme Corp", memory)
    # Pending facts must not appear in reusable texts.
    approved = [a.lower() for a in approved_experience_texts(memory)]
    assert "i closed a $2m enterprise deal with acme corp" not in approved
    # Claim checker still rejects fabricated client/metric style claims.
    result = check_claims(
        "I closed a $2M enterprise deal with Acme Corp and retention jumped by 37%.",
        memory,
    )
    assert result.safe is False


@pytest.mark.asyncio
async def test_multiple_angles_generated(user_memory: dict) -> None:
    provider = FakeProvider()
    agent = AngleFinderAgent(provider)
    result = await agent.run(
        AngleFinderInput(
            topic="local AI evaluation loops",
            content_mode="engineer",
            user_memory=user_memory,
            extra={"audience": "ML engineers"},
        )
    )
    assert len(result.angles) >= 3
    for angle in result.angles:
        assert angle.hook
        assert angle.type
        assert angle.reason
        assert angle.target_audience
    # Unique hooks
    hooks = [a.hook for a in result.angles]
    assert len(set(hooks)) == len(hooks)


@pytest.mark.asyncio
async def test_memory_builder_never_auto_approves(user_memory: dict) -> None:
    from agents.memory_builder import MemoryBuilderAgent, MemoryBuilderInput

    agent = MemoryBuilderAgent()
    proposed = await agent.run(
        MemoryBuilderInput(
            action="propose",
            statement="Shipped an internal eval harness for local models",
            category="experiment",
            persist=False,
            user_memory=user_memory,
        )
    )
    assert proposed.changed["approved"] is False
    assert all(item.get("id") != proposed.changed["id"] for item in proposed.verified)

    approved = await agent.run(
        MemoryBuilderInput(
            action="approve",
            experience_id=proposed.changed["id"],
            persist=False,
            user_memory={
                **normalize_memory(user_memory),
                "pending_experiences": proposed.pending,
                "verified_experiences": proposed.verified,
            },
        )
    )
    assert approved.changed["approved"] is True
    assert any(item["id"] == approved.changed["id"] for item in approved.verified)


def test_approve_moves_pending_to_verified(user_memory: dict) -> None:
    memory = normalize_memory(user_memory)
    memory, pending = propose_experience("Ran offline evals on Qwen drafts", memory=memory)
    assert any(item["id"] == pending["id"] for item in list_pending_experiences(memory))
    memory, verified = approve_experience(pending["id"], memory=memory)
    assert verified["approved"] is True
    assert verified["reusable"] is True
    assert any(item["id"] == verified["id"] for item in list_verified_experiences(memory))
    assert all(item["id"] != pending["id"] for item in list_pending_experiences(memory))
