"""Provider factory with DeepSeek/Qwen routing."""

from __future__ import annotations

from apps.api.config import settings
from models.base import ModelProvider
from models.fake import FakeProvider
from models.router import (
    RouterCallRecorder,
    build_family_provider,
    family_for_stage,
    provider_for_stage as routed_provider_for_stage,
)


def build_base_provider(*, fake: bool = False) -> ModelProvider:
    """Legacy helper — defaults to Qwen writing provider."""
    if fake or settings.use_fake_provider:
        return FakeProvider()
    return build_family_provider("qwen", fake=False)


def provider_for_stage(
    stage: str,
    *,
    fake: bool = False,
    recorder: RouterCallRecorder | None = None,
) -> ModelProvider:
    """Route stage to DeepSeek (reasoning) or Qwen (writing)."""
    return routed_provider_for_stage(stage, fake=fake, recorder=recorder)


def stage_family(stage: str) -> str:
    return family_for_stage(stage)
