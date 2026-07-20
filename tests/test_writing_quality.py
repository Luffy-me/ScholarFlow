"""AI Writing Quality Framework tests."""

from __future__ import annotations

import pytest

from agents.grounding import check_claims
from agents.writing_quality import (
    WritingQualityAnalyzer,
    WritingQualityInput,
    analyze_writing_quality,
)
from models.fake import FakeProvider


def test_generic_opening_has_high_ai_pattern_risk() -> None:
    text = "In today's rapidly evolving world, AI is revolutionizing industries."
    result = analyze_writing_quality(text, content_mode="founder")
    assert result.ai_pattern_risk >= 70
    assert any(p.category == "generic_opening" for p in result.detected_patterns)
    assert result.human_quality_score < 50


def test_personal_observation_has_higher_human_quality() -> None:
    generic = analyze_writing_quality(
        "In today's rapidly evolving world, AI is revolutionizing industries."
    )
    human = analyze_writing_quality(
        "I tested Qwen locally on my MacBook and noticed that workflow design "
        "mattered more than model size."
    )
    assert human.human_quality_score > generic.human_quality_score
    assert human.human_quality_score >= 65
    assert human.ai_pattern_risk < generic.ai_pattern_risk
    assert any(
        p in (human.data.get("preferred_patterns_found") or [])
        for p in ("personal_observation", "specific_details")
    )


def test_vague_claim_detected() -> None:
    text = "Studies show AI will replace all developers."
    result = analyze_writing_quality(text)
    categories = {p.category for p in result.detected_patterns}
    assert "vague_claims" in categories
    assert "unnatural_certainty" in categories
    assert result.ai_pattern_risk >= 70


def test_verified_project_experience_allowed() -> None:
    text = "I built ScholarFlow using RAG architecture."
    verified = ["I built ScholarFlow using RAG architecture", "Built ScholarFlow using RAG"]
    result = analyze_writing_quality(
        text,
        verified_memory=verified,
        user_memory={
            "projects": ["ScholarFlow"],
            "experiences": [],
            "verified_experiences": [],
            "pending_experiences": [],
        },
    )
    grounding = check_claims(
        text,
        {
            "projects": ["ScholarFlow"],
            "experiences": verified,
            "verified_experiences": [
                {
                    "id": "exp_scholarflow",
                    "statement": "I built ScholarFlow using RAG architecture",
                    "approved": True,
                    "reusable": True,
                    "category": "project",
                    "source": "user_provided",
                }
            ],
        },
    )
    assert grounding.safe is True
    assert not any(p.category == "fake_sources" for p in result.detected_patterns)
    assert result.human_quality_score >= 55


def test_unverified_scale_claim_rejected() -> None:
    text = "I helped 10000 users increase productivity."
    result = analyze_writing_quality(text, verified_memory=[])
    categories = {p.category for p in result.detected_patterns}
    assert "fake_sources" in categories
    assert result.ai_pattern_risk >= 70
    assert any("metric" in imp.lower() or "user" in imp.lower() or "verify" in imp.lower() for imp in result.improvements)


@pytest.mark.asyncio
async def test_analyzer_agent_output_shape(provider: FakeProvider) -> None:
    agent = WritingQualityAnalyzer(provider)
    result = await agent.run(
        WritingQualityInput(
            content="I tested Qwen locally on my MacBook and noticed workflow design mattered.",
            content_mode="engineer",
            verified_memory=["Compared local LLM workflows with cloud APIs for content drafting"],
        )
    )
    payload = result.as_report()
    assert set(payload) >= {
        "human_quality_score",
        "ai_pattern_risk",
        "specificity_score",
        "originality_score",
        "detected_patterns",
        "improvements",
    }
    assert isinstance(payload["detected_patterns"], list)
    assert result.human_quality_score >= 60


def test_framework_never_claims_authorship() -> None:
    result = analyze_writing_quality(
        "In today's rapidly evolving world, AI is revolutionizing industries."
    )
    blob = " ".join(result.improvements + [p.explanation for p in result.detected_patterns]).lower()
    assert "written by ai" not in blob
    assert "this was written by" not in blob
    disclaimer = (result.data.get("disclaimer") or "").lower()
    assert "written by ai" not in disclaimer
    assert "never label authorship" in disclaimer or "never claim" in disclaimer
