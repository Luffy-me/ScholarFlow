"""Ollama HTTP provider."""

from __future__ import annotations

from typing import Any

import httpx

from models.base import ChatMessage, GenerateResult, ModelProvider, ProviderHealth


class OllamaProvider(ModelProvider):
    name = "ollama"

    def __init__(self, base_url: str = "http://localhost:11434", default_model: str = "qwen2.5:7b") -> None:
        self.base_url = base_url.rstrip("/")
        self.default_model = default_model

    async def health(self) -> ProviderHealth:
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(f"{self.base_url}/api/tags")
                response.raise_for_status()
                payload = response.json()
                models = [item.get("name", "") for item in payload.get("models", []) if item.get("name")]
                return ProviderHealth(online=True, provider=self.name, models=models, detail="ok")
        except Exception as exc:  # noqa: BLE001 - surface provider status, don't crash callers
            return ProviderHealth(online=False, provider=self.name, models=[], detail=str(exc))

    async def generate(
        self,
        messages: list[ChatMessage],
        *,
        model: str | None = None,
        temperature: float = 0.4,
        response_format: str | None = None,
    ) -> GenerateResult:
        selected = model or self.default_model
        body: dict[str, Any] = {
            "model": selected,
            "messages": [{"role": m.role, "content": m.content} for m in messages],
            "stream": False,
            "options": {"temperature": temperature},
        }
        if response_format == "json":
            body["format"] = "json"

        async with httpx.AsyncClient(timeout=120.0) as client:
            response = await client.post(f"{self.base_url}/api/chat", json=body)
            response.raise_for_status()
            payload = response.json()

        message = payload.get("message") or {}
        text = str(message.get("content") or "")
        return GenerateResult(text=text, model=selected, provider=self.name, raw=payload)
