"""Capability-based model orchestrator tests."""

from __future__ import annotations

from models.capabilities import Capability
from models.orchestrator import ModelOrchestrator


def test_orchestrator_routes_capabilities_to_families() -> None:
    orch = ModelOrchestrator(fake=True)
    writing = orch.select_for_capability(Capability.WRITING)
    critique = orch.select_for_capability(Capability.CRITIQUE)
    reasoning = orch.select_for_capability(Capability.REASONING)
    extraction = orch.select_for_capability(Capability.EXTRACTION)
    ranking = orch.select_for_capability(Capability.RANKING)
    summarization = orch.select_for_capability(Capability.SUMMARIZATION)

    assert writing.family == "qwen"
    assert summarization.family == "qwen"
    assert critique.family == "deepseek"
    assert reasoning.family == "deepseek"
    assert extraction.family == "deepseek"
    assert ranking.family == "deepseek"
    assert orch.decision_log()


def test_orchestrator_provider_for_stage_and_agent() -> None:
    orch = ModelOrchestrator(fake=True)

    class DummyAgent:
        name = "insight_engine"
        capabilities = [Capability.REASONING]

    provider = orch.provider_for_agent(DummyAgent())
    assert getattr(provider, "family", "") == "deepseek"
    writer = orch.provider_for_stage("writer")
    assert getattr(writer, "family", "") == "qwen"
