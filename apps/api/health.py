"""Aggregate health for GET /health."""

from __future__ import annotations

from typing import Any

from sqlalchemy import text

from apps.api.config import settings
from apps.api.ollama_probe import missing_models, probe_ollama
from database.session import create_db_engine, init_db


async def build_health_payload() -> dict[str, Any]:
    writer = settings.model_for_stage("writer")
    critic = settings.model_for_stage("critic")
    predictor = settings.model_for_stage("predictor")
    # Preserve order, drop duplicates (critic/predictor often share a tag).
    required: list[str] = []
    for m in (writer, critic, predictor):
        if m not in required:
            required.append(m)

    database_ok = True
    try:
        with create_db_engine(settings.database_url).connect() as conn:
            conn.execute(text("SELECT 1"))
    except Exception:  # noqa: BLE001
        database_ok = False

    backend_ok = database_ok

    if settings.use_fake_provider:
        return {
            "status": "healthy",
            "ok": True,
            "backend": backend_ok,
            "database": database_ok,
            "ollama": True,
            "models": required,
            "installed_models": ["fake"],
            "fake_provider": True,
        }

    probe = await probe_ollama(settings.ollama_base_url)
    ollama_ok = probe.reachable
    installed = probe.installed_models
    present_required = [m for m in required if m not in missing_models(installed, [m])]

    if backend_ok and ollama_ok and len(present_required) == len(required):
        status = "healthy"
    elif backend_ok:
        status = "degraded"
    else:
        status = "unhealthy"

    payload: dict[str, Any] = {
        "status": status,
        "ok": status in {"healthy", "degraded"},
        "backend": backend_ok,
        "database": database_ok,
        "ollama": ollama_ok,
        "models": present_required if ollama_ok else required,
        "installed_models": installed,
        "required_models": required,
    }
    if probe.message and not ollama_ok:
        payload["detail"] = probe.message
        payload["resolution"] = probe.resolution
    if ollama_ok and missing_models(installed, required):
        payload["missing_models"] = missing_models(installed, required)
    return payload
