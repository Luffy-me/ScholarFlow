"""DeepSeek/Qwen model routing tests."""

from __future__ import annotations

import pytest

from agents.humanizer import HumanizerAgent, HumanizerInput
from agents.insight_engine import InsightEngineAgent, InsightEngineInput
from agents.researcher import ResearcherAgent, ResearcherInput
from agents.writer import WriterAgent, WriterInput
from apps.api.config import Settings
from models.deepseek.presets import DEEPSEEK_DEFAULT_MODEL
from models.deepseek_provider import DeepSeekProvider
from models.router import (
    RouterCallRecorder,
    family_for_stage,
    is_deepseek_model,
    is_qwen_model,
    provider_for_stage,
    resolve_model_name,
)


def test_deepseek_assigned_to_reasoning_stages() -> None:
    for stage in (
        "researcher",
        "research_agent",
        "trend_analysis",
        "trend_analyzer",
        "insight_engine",
        "claim_checker",
        "critic",
        "engagement_predictor",
        "predictor",
    ):
        assert family_for_stage(stage) == "deepseek"
        assert is_deepseek_model(resolve_model_name(stage))


def test_qwen_assigned_to_writing_stages() -> None:
    for stage in ("writer", "humanizer", "debate_rewrite"):
        assert family_for_stage(stage) == "qwen"
        assert is_qwen_model(resolve_model_name(stage))


def test_env_aliases_resolve_deepseek_and_qwen(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("WRITER_MODEL", "qwen3:8b")
    monkeypatch.setenv("HUMANIZER_MODEL", "qwen3:8b")
    monkeypatch.setenv("RESEARCH_MODEL", "deepseek")
    monkeypatch.setenv("INSIGHT_MODEL", "deepseek")
    monkeypatch.setenv("CRITIC_MODEL", "deepseek")
    monkeypatch.setenv("PREDICTOR_MODEL", "deepseek")
    monkeypatch.setenv("DEEPSEEK_MODEL", DEEPSEEK_DEFAULT_MODEL)

    cfg = Settings()
    assert cfg.model_for_stage("writer") == "qwen3:8b"
    assert cfg.model_for_stage("humanizer") == "qwen3:8b"
    assert cfg.model_for_stage("researcher") == DEEPSEEK_DEFAULT_MODEL
    assert cfg.model_for_stage("insight_engine") == DEEPSEEK_DEFAULT_MODEL
    assert cfg.model_for_stage("critic") == DEEPSEEK_DEFAULT_MODEL
    assert cfg.model_for_stage("predictor") == DEEPSEEK_DEFAULT_MODEL


@pytest.mark.asyncio
async def test_runtime_providers_use_correct_families() -> None:
    recorder = RouterCallRecorder()
    research_provider = provider_for_stage("researcher", fake=True, recorder=recorder)
    insight_provider = provider_for_stage("insight_engine", fake=True, recorder=recorder)
    writer_provider = provider_for_stage("writer", fake=True, recorder=recorder)
    humanizer_provider = provider_for_stage("humanizer", fake=True, recorder=recorder)

    research = await ResearcherAgent(research_provider).run(
        ResearcherInput(topic="local evaluation loops", content_mode="engineer")
    )
    insight = await InsightEngineAgent(insight_provider).run(
        InsightEngineInput(
            topic="local evaluation loops",
            content_mode="engineer",
            extra={
                "verified_experiences": ["Compared local LLM workflows with cloud APIs"],
                "research": research.data,
            },
        )
    )
    written = await WriterAgent(writer_provider).run(
        WriterInput(topic="local evaluation loops", content_mode="engineer")
    )
    humanized = await HumanizerAgent(humanizer_provider).run(
        HumanizerInput(text=written.text, topic="local evaluation loops")
    )

    # Routed fake providers relabel provider to family name.
    assert any(c["family"] == "deepseek" and c["stage"] == "researcher" for c in recorder.calls)
    assert any(c["family"] == "deepseek" and c["stage"] == "insight_engine" for c in recorder.calls)
    assert any(c["family"] == "qwen" and c["stage"] == "writer" for c in recorder.calls)
    assert any(c["family"] == "qwen" and c["stage"] == "humanizer" for c in recorder.calls)
    assert insight.meta.get("reasoning_family") == "deepseek"
    assert humanized.text.strip()


def test_deepseek_provider_identity() -> None:
    provider = DeepSeekProvider(default_model=DEEPSEEK_DEFAULT_MODEL)
    assert provider.name == "deepseek"
    assert "deepseek" in provider.default_model.lower()
