"""Build AI status payload for /api/v1/ai/status."""

from __future__ import annotations

from typing import Any

from apps.api import ai_config
from apps.api.config import settings
from apps.api.ollama_probe import missing_models, probe_ollama, resolution_for_missing


async def build_ai_status_payload() -> dict[str, Any]:
    writer = settings.model_for_stage("writer")
    humanizer = settings.model_for_stage("humanizer")
    critic = settings.model_for_stage("critic")
    predictor = settings.model_for_stage("predictor")

    if settings.use_fake_provider:
        return {
            "connected": True,
            "online": True,
            "provider": "fake",
            "writer": writer,
            "humanizer": humanizer,
            "critic": critic,
            "predictor": predictor,
            "models": ["fake"],
            "installed_models": ["fake"],
            "default_model": settings.default_model,
            "detail": "USE_FAKE_PROVIDER=true — Ollama not used.",
            "missing_models": [],
            "errors": [],
        }

    probe = await probe_ollama(settings.ollama_base_url)
    installed = probe.installed_models
    required = [writer, critic, predictor]
    missing = missing_models(installed, required) if probe.reachable else required

    errors: list[dict[str, str]] = []
    if probe.error:
        errors.append(
            {
                "error": probe.error,
                "message": probe.message or "Ollama is not available.",
                "resolution": probe.resolution or "Run: ollama serve",
            }
        )
    for model in missing:
        errors.append(
            {
                "error": "ModelNotFound",
                "message": f"{model} is not installed.",
                "resolution": resolution_for_missing(model),
            }
        )

    connected = probe.reachable and not missing
    detail = "ok" if connected else (errors[0]["message"] if errors else "Ollama unavailable")

    return {
        "connected": connected,
        "online": probe.reachable,
        "provider": "ollama",
        "writer": writer,
        "humanizer": humanizer,
        "critic": critic,
        "predictor": predictor,
        "models": installed,
        "installed_models": installed,
        "default_model": settings.default_model,
        "detail": detail,
        "missing_models": missing,
        "errors": errors,
        "ollama_base_url": settings.ollama_base_url,
        "required_models": list(ai_config.REQUIRED_OLLAMA_MODELS),
    }
