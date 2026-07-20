"""DeepSeek reasoning provider.

Runs DeepSeek models through the local Ollama runtime by default.
Agents should use this for analysis, criticism, and insight generation —
not for final human-voice writing (that stays on Qwen).
"""

from __future__ import annotations

from models.base import ChatMessage, GenerateResult, ModelProvider, ProviderHealth
from models.deepseek.presets import DEEPSEEK_DEFAULT_MODEL
from models.ollama.provider import OllamaProvider


class DeepSeekProvider(ModelProvider):
    """Reasoning-focused provider backed by Ollama DeepSeek models."""

    name = "deepseek"

    def __init__(
        self,
        base_url: str = "http://127.0.0.1:11434",
        default_model: str = DEEPSEEK_DEFAULT_MODEL,
        *,
        timeout_seconds: float = 300.0,
        think: bool = True,
        num_ctx: int = 4096,
    ) -> None:
        # DeepSeek-R1 benefits from think=True for reasoning traces when available.
        self.default_model = default_model or DEEPSEEK_DEFAULT_MODEL
        self._ollama = OllamaProvider(
            base_url=base_url,
            default_model=self.default_model,
            timeout_seconds=timeout_seconds,
            think=think,
            num_ctx=num_ctx,
        )

    async def health(self) -> ProviderHealth:
        status = await self._ollama.health()
        return ProviderHealth(
            online=status.online,
            provider=self.name,
            models=status.models,
            detail=status.detail,
        )

    async def ensure_available(self, model: str | None = None) -> ProviderHealth:
        return await self._ollama.ensure_available(model or self.default_model)

    async def generate(
        self,
        messages: list[ChatMessage],
        *,
        model: str | None = None,
        temperature: float = 0.3,
        response_format: str | None = None,
    ) -> GenerateResult:
        selected = model or self.default_model
        result = await self._ollama.generate(
            messages,
            model=selected,
            temperature=temperature,
            response_format=response_format,
        )
        # Relabel provider so routing/tests can distinguish DeepSeek reasoning calls.
        return GenerateResult(
            text=result.text,
            model=result.model,
            provider=self.name,
            raw=result.raw,
        )
