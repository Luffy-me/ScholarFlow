"""Ollama HTTP provider with availability detection."""

from __future__ import annotations

import asyncio
from typing import Any

import httpx

from models.base import ChatMessage, GenerateResult, ModelProvider, ProviderHealth
from models.ollama.http_client import ollama_client, ollama_timeout


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
        connect_timeout_seconds: float = 5.0,
        max_retries: int = 2,
        think: bool = False,
        num_ctx: int = 4096,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.default_model = default_model
        self.timeout_seconds = timeout_seconds
        self.connect_timeout_seconds = connect_timeout_seconds
        self.max_retries = max(0, max_retries)
        self.think = think
        self.num_ctx = num_ctx

    def _health_timeout(self) -> httpx.Timeout:
        return ollama_timeout(connect=self.connect_timeout_seconds, read=self.connect_timeout_seconds + 5)

    def _generate_timeout(self) -> httpx.Timeout:
        return ollama_timeout(connect=self.connect_timeout_seconds, read=self.timeout_seconds)

    async def health(self) -> ProviderHealth:
        try:
            async with ollama_client(timeout=self._health_timeout()) as client:
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
        except httpx.TimeoutException:
            return ProviderHealth(
                online=False,
                provider=self.name,
                models=[],
                detail=(
                    f"Ollama unavailable: connection timeout after "
                    f"{self.connect_timeout_seconds:.0f} seconds at {self.base_url}"
                ),
            )
        except httpx.ConnectError:
            return ProviderHealth(
                online=False,
                provider=self.name,
                models=[],
                detail=f"Ollama unavailable: cannot connect to {self.base_url}",
            )
        except Exception as exc:  # noqa: BLE001
            return ProviderHealth(
                online=False,
                provider=self.name,
                models=[],
                detail=f"Ollama unavailable at {self.base_url}: {exc}",
            )

    async def ensure_available(self, model: str | None = None) -> ProviderHealth:
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

        last_error: Exception | None = None
        for attempt in range(self.max_retries + 1):
            try:
                async with ollama_client(timeout=self._generate_timeout()) as client:
                    response = await client.post(f"{self.base_url}/api/chat", json=body)
                    response.raise_for_status()
                    payload = response.json()
                break
            except httpx.TimeoutException as exc:
                last_error = exc
                if attempt < self.max_retries:
                    await asyncio.sleep(0.4 * (attempt + 1))
                    continue
                raise OllamaUnavailableError(
                    f"Ollama unavailable: request timeout after {self.timeout_seconds:.0f} seconds"
                ) from exc
            except httpx.ConnectError as exc:
                last_error = exc
                if attempt < self.max_retries:
                    await asyncio.sleep(0.4 * (attempt + 1))
                    continue
                raise OllamaUnavailableError(
                    f"Ollama unavailable: connection failed after {self.max_retries + 1} attempts"
                ) from exc
            except httpx.HTTPStatusError as exc:
                raise OllamaUnavailableError(
                    f"Ollama returned HTTP {exc.response.status_code} for model {selected}"
                ) from exc
        else:
            raise OllamaUnavailableError(str(last_error or "Ollama request failed"))

        message = payload.get("message") or {}
        text = str(message.get("content") or "").strip()
        if not text:
            text = str(message.get("thinking") or "").strip()
        if not text:
            raise OllamaUnavailableError(f"Ollama returned empty content for model {selected}")
        return GenerateResult(text=text, model=selected, provider=self.name, raw=payload)

    @staticmethod
    def _model_available(installed: list[str], requested: str) -> bool:
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
