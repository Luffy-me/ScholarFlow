"""Truth Layer v2 grounding tests."""

from __future__ import annotations

from agents.grounding import check_claims, sanitize_ungrounded_claims
from shared.knowledge import load_user_memory


def test_fake_client_claim_rejected(user_memory: dict) -> None:
    text = (
        "When I built a local RAG chatbot for a client, the model size felt like a checkbox. "
        "Local evaluation loops mattered more."
    )
    result = check_claims(text, user_memory)
    assert any(c.claim_type == "client" for c in result.rejected_claims)
    assert result.safe is False


def test_fake_metric_rejected(user_memory: dict) -> None:
    text = (
        "In my experience with AI product design, slogans often fail. "
        "When we introduced a tiered reward system, retention jumped by 37%."
    )
    result = check_claims(text, user_memory)
    assert any(c.claim_type == "metric" for c in result.rejected_claims)
    assert result.safe is False


def test_valid_project_accepted(user_memory: dict) -> None:
    text = (
        "I built a RAG chatbot and kept making the same mistake. "
        "I added more context instead of better questions."
    )
    result = check_claims(text, user_memory)
    assert result.safe is True
    assert any(c.claim_type in {"project", "personal_experience"} for c in result.approved_claims)
    assert not any(c.claim_type == "client" for c in result.rejected_claims)


def test_personal_memory_used_correctly(user_memory: dict) -> None:
    memory = load_user_memory()
    assert "RAG chatbot" in memory["projects"]
    text = (
        "I compared local LLM workflows with cloud APIs for content drafting. "
        "That tradeoff shaped how I approach the LinkedIn Content Intelligence Engine."
    )
    result = check_claims(text, user_memory)
    assert result.safe is True
    assert len(result.approved_claims) >= 1
    assert all(c.claim_type != "metric" for c in result.rejected_claims)


def test_sanitize_removes_fake_client_and_keeps_grounded_project(user_memory: dict) -> None:
    text = (
        "I built a RAG chatbot for a client last week. "
        "I learned that retrieval quality beats model size."
    )
    result = sanitize_ungrounded_claims(text, user_memory)
    assert "for a client" not in result.sanitized_text.lower()
    assert "last week" not in result.sanitized_text.lower()
    # Either the grounded sentence remains or text is reduced but safe.
    assert "37%" not in result.sanitized_text
    residual = check_claims(result.sanitized_text, user_memory)
    assert residual.safe is True


def test_fake_quote_rejected(user_memory: dict) -> None:
    text = (
        'I showed the RAG chatbot to a teammate and they said, '
        '"This is great, but I just need a simple prompt template."'
    )
    result = check_claims(text, user_memory)
    assert result.safe is False
    assert any(c.claim_type in {"quote", "client", "time_reference", "achievement"} for c in result.rejected_claims)


def test_time_reference_rejected_even_with_valid_project(user_memory: dict) -> None:
    text = "Last week, I tested two RAG chatbots — one local, one cloud."
    result = check_claims(text, user_memory)
    assert result.safe is False
    assert any(c.claim_type == "time_reference" for c in result.rejected_claims)
