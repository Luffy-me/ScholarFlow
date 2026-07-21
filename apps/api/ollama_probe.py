"""Ollama reachability and model inventory (server-side only)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import httpx

from models.ollama.http_client import ollama_client, ollama_timeout
from models.ollama.provider import OllamaProvider


@dataclass(frozen=True)
class OllamaProbeResult:
    reachable: bool
    installed_models: list[str]
    error: str | None = None
    message: str | None = None
    resolution: str | None = None


def model_installed(installed: list[str], requested: str) -> bool:
    return OllamaProvider._model_available(installed, requested)  # noqa: SLF001


async def probe_ollama(base_url: str, *, timeout: float = 5.0) -> OllamaProbeResult:
    url = base_url.rstrip("/")
    try:
        timeout = ollama_timeout(connect=timeout, read=timeout + 5)
        async with ollama_client(timeout=timeout) as client:
            response = await client.get(f"{url}/api/tags")
            response.raise_for_status()
            payload: dict[str, Any] = response.json()
            models = [
                str(item.get("name", ""))
                for item in payload.get("models", [])
                if item.get("name")
            ]
            return OllamaProbeResult(reachable=True, installed_models=models)
    except httpx.TimeoutException:
        return OllamaProbeResult(
            reachable=False,
            installed_models=[],
            error="OllamaTimeout",
            message=f"Ollama unavailable: connection timeout after {timeout:.0f} seconds at {url}.",
            resolution="Ensure Ollama is running: ollama serve",
        )
    except httpx.ConnectError:
        return OllamaProbeResult(
            reachable=False,
            installed_models=[],
            error="OllamaOffline",
            message=f"Cannot reach Ollama at {url}.",
            resolution="Start Ollama in another terminal: ollama serve",
        )
    except httpx.HTTPStatusError as exc:
        return OllamaProbeResult(
            reachable=False,
            installed_models=[],
            error="OllamaInvalidResponse",
            message=f"Ollama returned HTTP {exc.response.status_code}.",
            resolution="Check OLLAMA_BASE_URL and restart Ollama.",
        )
    except Exception as exc:  # noqa: BLE001
        return OllamaProbeResult(
            reachable=False,
            installed_models=[],
            error="OllamaUnreachable",
            message=str(exc) or "Unknown error talking to Ollama.",
            resolution="Verify OLLAMA_BASE_URL and that ollama serve is running.",
        )


def missing_models(installed: list[str], required: list[str]) -> list[str]:
    return [m for m in required if not model_installed(installed, m)]


def resolution_for_missing(model: str) -> str:
    return f"Run: ollama pull {model}"
