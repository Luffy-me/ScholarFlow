"""AI status endpoint tests."""

from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest
from httpx import ASGITransport, AsyncClient

from apps.api.config import settings
from apps.api.main import app
from apps.api.ollama_probe import OllamaProbeResult


@pytest.mark.asyncio
async def test_ai_status_ollama_offline_never_500() -> None:
    offline = OllamaProbeResult(
        reachable=False,
        installed_models=[],
        error="OllamaOffline",
        message="Cannot reach Ollama",
        resolution="Run: ollama serve",
    )
    with patch("apps.api.ai_status.probe_ollama", new=AsyncMock(return_value=offline)):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            res = await client.get("/api/v1/ai/status")
    assert res.status_code == 200
    body = res.json()
    assert body["connected"] is False
    assert body["writer"] == settings.model_for_stage("writer")
    assert body["critic"] == settings.model_for_stage("critic")
    assert body["errors"][0]["error"] == "OllamaOffline"


@pytest.mark.asyncio
async def test_health_ok() -> None:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        res = await client.get("/health")
    assert res.status_code == 200
    assert res.json() == {"status": "ok"}
