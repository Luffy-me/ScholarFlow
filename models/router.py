"""Model router: DeepSeek for reasoning, Qwen for human writing."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal

from models.base import ChatMessage, GenerateResult, ModelProvider, ProviderHealth
from models.deepseek.presets import DEEPSEEK_DEFAULT_MODEL
from models.deepseek_provider import DeepSeekProvider
from models.fake import FakeProvider
from models.ollama import OllamaProvider


def _settings():
    from apps.api.config import settings

    return settings

Family = Literal["deepseek", "qwen"]

# Reasoning / analysis / criticism
DEEPSEEK_STAGES: frozenset[str] = frozenset(
    {
        "researcher",
        "research_agent",
        "research",
        "trend_analyzer",
        "trend_analysis",
        "insight_engine",
        "insight",
        "claim_checker",
        "grounding",
        "critic",
        "engagement_predictor",
        "predictor",
        "writing_quality",
        "angle_finder",
        "strategist",
        "debate_critic",
        "debate_final",
    }
)

# Human writing voice
QWEN_STAGES: frozenset[str] = frozenset(
    {
        "writer",
        "humanizer",
        "debate_rewrite",
    }
)


def family_for_stage(stage: str) -> Family:
    key = (stage or "").strip().lower()
    if key in QWEN_STAGES:
        return "qwen"
    if key in DEEPSEEK_STAGES:
        return "deepseek"
    # Default unknown stages to reasoning family.
    return "deepseek"


def resolve_model_name(stage: str) -> str:
    """Resolve concrete model id for a pipeline stage.

    Family wins over stale env overrides: a DeepSeek stage never keeps a Qwen
    model name, and a Qwen writing stage never keeps a DeepSeek model name.
    """
    settings = _settings()
    family = family_for_stage(stage)
    model = settings.model_for_stage(stage)
    if family == "deepseek" and not is_deepseek_model(model):
        return settings.resolved_deepseek_model()
    if family == "qwen" and not is_qwen_model(model):
        return settings.writer_model or settings.ollama_model or "qwen3:8b"
    return model


def is_deepseek_model(model_name: str) -> bool:
    name = (model_name or "").lower()
    return "deepseek" in name


def is_qwen_model(model_name: str) -> bool:
    name = (model_name or "").lower()
    return "qwen" in name


@dataclass
class RoutedProvider(ModelProvider):
    """Provider wrapper that pins family + model and records calls for tests."""

    base: ModelProvider
    stage: str
    family: Family
    stage_model: str
    name: str = "routed"
    call_log: list[dict[str, str]] = field(default_factory=list)

    async def health(self) -> ProviderHealth:
        return await self.base.health()

    async def generate(
        self,
        messages: list[ChatMessage],
        *,
        model: str | None = None,
        temperature: float = 0.4,
        response_format: str | None = None,
    ) -> GenerateResult:
        selected = model or self.stage_model
        self.call_log.append(
            {
                "stage": self.stage,
                "family": self.family,
                "model": selected,
                "provider": getattr(self.base, "name", self.name),
            }
        )
        result = await self.base.generate(
            messages,
            model=selected,
            temperature=temperature,
            response_format=response_format,
        )
        # Preserve family identity even when FakeProvider is the base.
        provider_name = self.family if isinstance(self.base, FakeProvider) else result.provider
        return GenerateResult(
            text=result.text,
            model=selected or result.model,
            provider=provider_name,
            raw={**result.raw, "stage": self.stage, "family": self.family},
        )


@dataclass
class RouterCallRecorder:
    """Shared call log across stage providers in one pipeline run."""

    calls: list[dict[str, str]] = field(default_factory=list)

    def record(self, entry: dict[str, str]) -> None:
        self.calls.append(entry)

    def families_used(self) -> set[str]:
        return {c.get("family", "") for c in self.calls}

    def stages_for_family(self, family: Family) -> list[str]:
        return [c["stage"] for c in self.calls if c.get("family") == family]


def build_family_provider(family: Family, *, fake: bool = False) -> ModelProvider:
    settings = _settings()
    if fake or settings.use_fake_provider:
        return FakeProvider()
    if family == "deepseek":
        return DeepSeekProvider(
            base_url=settings.ollama_base_url,
            default_model=settings.resolved_deepseek_model(),
            think=True,
            num_ctx=settings.ollama_num_ctx,
        )
    return OllamaProvider(
        base_url=settings.ollama_base_url,
        default_model=settings.writer_model or settings.ollama_model,
        think=settings.ollama_think,
        num_ctx=settings.ollama_num_ctx,
    )


def provider_for_stage(
    stage: str,
    *,
    fake: bool = False,
    recorder: RouterCallRecorder | None = None,
) -> ModelProvider:
    """Return a provider routed to DeepSeek (reasoning) or Qwen (writing)."""
    family = family_for_stage(stage)
    model_name = resolve_model_name(stage)
    base = build_family_provider(family, fake=fake)

    routed = RoutedProvider(
        base=base,
        stage=stage,
        family=family,
        stage_model=model_name,
        name=f"{family}:{stage}",
    )

    if recorder is not None:
        original_generate = routed.generate

        async def _generate(
            messages: list[ChatMessage],
            *,
            model: str | None = None,
            temperature: float = 0.4,
            response_format: str | None = None,
        ) -> GenerateResult:
            result = await original_generate(
                messages,
                model=model,
                temperature=temperature,
                response_format=response_format,
            )
            recorder.record(
                {
                    "stage": stage,
                    "family": family,
                    "model": result.model,
                    "provider": result.provider,
                }
            )
            return result

        routed.generate = _generate  # type: ignore[method-assign]

    return routed


def default_deepseek_model() -> str:
    return DEEPSEEK_DEFAULT_MODEL
