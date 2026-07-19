"""Provider factory with optional per-stage model routing."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from apps.api.config import settings
from models.base import ChatMessage, GenerateResult, ModelProvider, ProviderHealth
from models.fake import FakeProvider
from models.ollama import OllamaProvider


@dataclass
class StageRoutedProvider(ModelProvider):
    """Wraps a base provider and overrides the model name per pipeline stage."""

    base: ModelProvider
    stage_model: str
    name: str = "routed"

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
        return await self.base.generate(
            messages,
            model=model or self.stage_model,
            temperature=temperature,
            response_format=response_format,
        )


def build_base_provider(*, fake: bool = False) -> ModelProvider:
    if fake or settings.use_fake_provider:
        return FakeProvider()
    return OllamaProvider(
        base_url=settings.ollama_base_url,
        default_model=settings.ollama_model,
        think=settings.ollama_think,
        num_ctx=settings.ollama_num_ctx,
    )


def provider_for_stage(stage: str, *, fake: bool = False) -> ModelProvider:
    base = build_base_provider(fake=fake)
    if isinstance(base, FakeProvider):
        return base
    return StageRoutedProvider(base=base, stage_model=settings.model_for_stage(stage), name=f"ollama:{stage}")
