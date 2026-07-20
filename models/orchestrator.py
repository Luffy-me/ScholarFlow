"""Capability-based model orchestrator.

Agents request capabilities; the orchestrator returns a provider.
Agents never import concrete model backends.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from models.base import ModelProvider
from models.capabilities import (
    CAPABILITY_FAMILY_PREFERENCE,
    STAGE_CAPABILITIES,
    Capability,
)
from models.router import RouterCallRecorder, family_for_stage, provider_for_stage, resolve_model_name

# Map capability → canonical pipeline stage used for family/model resolution.
_CAPABILITY_STAGE: dict[Capability, str] = {
    Capability.REASONING: "insight_engine",
    Capability.WRITING: "writer",
    Capability.CLASSIFICATION: "writer",
    Capability.SUMMARIZATION: "humanizer",
    Capability.CRITIQUE: "critic",
    Capability.EXTRACTION: "claim_checker",
    Capability.RANKING: "predictor",
    Capability.RESEARCH: "researcher",
    Capability.TREND_DETECTION: "trend_analyzer",
}


@dataclass
class ProviderSelection:
    capability: Capability
    family: str
    model: str
    provider: ModelProvider
    stage: str = ""
    reason: str = ""


@dataclass
class ModelOrchestrator:
    """Select providers dynamically from declared capabilities."""

    fake: bool = False
    recorder: RouterCallRecorder = field(default_factory=RouterCallRecorder)
    selections: list[dict[str, Any]] = field(default_factory=list)

    def capability_for_stage(self, stage: str) -> Capability:
        key = (stage or "").strip().lower()
        return STAGE_CAPABILITIES.get(key, Capability.REASONING)

    def select_for_capability(
        self,
        capability: Capability | str,
        *,
        stage: str = "",
    ) -> ProviderSelection:
        if isinstance(capability, str):
            capability = Capability(capability)

        prefs = CAPABILITY_FAMILY_PREFERENCE.get(capability, ("deepseek", "qwen"))
        resolved_stage = (stage or "").strip() or _CAPABILITY_STAGE.get(capability, "insight_engine")

        # Prefer capability family mapping when stage family disagrees.
        stage_family = family_for_stage(resolved_stage)
        preferred_family = prefs[0]
        if stage_family != preferred_family and capability in {
            Capability.WRITING,
            Capability.SUMMARIZATION,
            Capability.CLASSIFICATION,
        }:
            resolved_stage = "writer" if capability != Capability.SUMMARIZATION else "humanizer"
        elif stage_family != preferred_family and capability in {
            Capability.REASONING,
            Capability.CRITIQUE,
            Capability.EXTRACTION,
            Capability.RANKING,
            Capability.RESEARCH,
            Capability.TREND_DETECTION,
        }:
            resolved_stage = _CAPABILITY_STAGE[capability]

        provider = provider_for_stage(
            resolved_stage, fake=self.fake, recorder=self.recorder
        )
        family = getattr(provider, "family", preferred_family)
        model = getattr(provider, "stage_model", resolve_model_name(resolved_stage))

        selection = ProviderSelection(
            capability=capability,
            family=family,
            model=model,
            provider=provider,
            stage=resolved_stage,
            reason=f"capability={capability.value}; prefs={prefs}; stage={resolved_stage}",
        )
        self.selections.append(
            {
                "capability": capability.value,
                "family": selection.family,
                "model": selection.model,
                "stage": resolved_stage,
                "reason": selection.reason,
            }
        )
        return selection

    def provider_for_stage(self, stage: str) -> ModelProvider:
        capability = self.capability_for_stage(stage)
        return self.select_for_capability(capability, stage=stage).provider

    def provider_for_agent(self, agent: Any) -> ModelProvider:
        """Resolve provider from an agent's declared `capabilities` attribute."""
        caps = getattr(agent, "capabilities", None) or getattr(type(agent), "capabilities", None)
        stage = str(getattr(agent, "name", "") or getattr(type(agent), "name", "") or "")
        if not caps:
            return self.provider_for_stage(stage or "insight_engine")
        primary = caps[0] if isinstance(caps, (list, tuple)) else caps
        return self.select_for_capability(primary, stage=stage).provider

    def decision_log(self) -> list[dict[str, Any]]:
        return list(self.selections)
