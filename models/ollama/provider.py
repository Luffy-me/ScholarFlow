"""Ollama HTTP provider with availability detection."""

from __future__ import annotations

from typing import Any

import httpx

from models.base import ChatMessage, GenerateResult, ModelProvider, ProviderHealth


class OllamaUnavailableError(RuntimeError):
    """Raised when Ollama is offline or the requested model is missing."""


class OllamaProvider(ModelProvider):
    name = "ollama"

    def __init__(
        self,
        base_url: str = "http://127.0.0.1:11434",
        default_model: str = "qwen3:8b",
        *,
        timeout_seconds: float = 300.0,
        think: bool = False,
        num_ctx: int = 4096,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.default_model = default_model
        self.timeout_seconds = timeout_seconds
        # Qwen3 "thinking" models otherwise spend tokens on hidden reasoning.
        self.think = think
        self.num_ctx = num_ctx

    async def health(self) -> ProviderHealth:
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(f"{self.base_url}/api/tags")
                response.raise_for_status()
                payload = response.json()
                models = [item.get("name", "") for item in payload.get("models", []) if item.get("name")]
                detail = "ok"
                if self.default_model and not self._model_available(models, self.default_model):
                    detail = (
                        f"Ollama online, but model '{self.default_model}' is not installed. "
                        f"Run: ollama pull {self.default_model}"
                    )
                return ProviderHealth(online=True, provider=self.name, models=models, detail=detail)
        except Exception as exc:  # noqa: BLE001 - surface provider status, don't crash callers
            return ProviderHealth(
                online=False,
                provider=self.name,
                models=[],
                detail=f"Ollama unavailable at {self.base_url}: {exc}",
            )

    async def ensure_available(self, model: str | None = None) -> ProviderHealth:
        """Fail fast with a clear error if Ollama or the model is unavailable."""
        status = await self.health()
        selected = model or self.default_model
        if not status.online:
            raise OllamaUnavailableError(status.detail or "Ollama is not reachable")
        if selected and not self._model_available(status.models, selected):
            raise OllamaUnavailableError(
                f"Model '{selected}' is not available locally. "
                f"Installed: {status.models or 'none'}. Run: ollama pull {selected}"
            )
        return status

    async def generate(
        self,
        messages: list[ChatMessage],
        *,
        model: str | None = None,
        temperature: float = 0.4,
        response_format: str | None = None,
    ) -> GenerateResult:
        selected = model or self.default_model
        await self.ensure_available(selected)

        body: dict[str, Any] = {
            "model": selected,
            "messages": [{"role": m.role, "content": m.content} for m in messages],
            "stream": False,
            "think": self.think,
            "options": {
                "temperature": temperature,
                "num_ctx": self.num_ctx,
            },
        }
        if response_format == "json":
            body["format"] = "json"

        async with httpx.AsyncClient(timeout=self.timeout_seconds) as client:
            response = await client.post(f"{self.base_url}/api/chat", json=body)
            response.raise_for_status()
            payload = response.json()

        message = payload.get("message") or {}
        text = str(message.get("content") or "").strip()
        if not text:
            # Fallback if a thinking model still returns empty content.
            text = str(message.get("thinking") or "").strip()
        return GenerateResult(text=text, model=selected, provider=self.name, raw=payload)

    @staticmethod
    def _model_available(installed: list[str], requested: str) -> bool:
        """Match exact names or tag-prefix equivalents (qwen3:8b vs qwen3:8b-...)."""
        requested_l = requested.lower()
        for name in installed:
            name_l = name.lower()
            if name_l == requested_l:
                return True
            if name_l.startswith(requested_l + "-") or name_l.startswith(requested_l + ":"):
                return True
            if name_l.split(":")[0] == requested_l.split(":")[0] and name_l.startswith(requested_l):
                return True
        return False
