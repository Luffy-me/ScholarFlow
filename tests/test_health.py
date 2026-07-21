"""Health endpoint tests."""

from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest
from httpx import ASGITransport, AsyncClient

from apps.api.main import app
from apps.api.ollama_probe import OllamaProbeResult


@pytest.mark.asyncio
async def test_health_returns_200_with_backend_flag() -> None:
    offline = OllamaProbeResult(reachable=False, installed_models=[], message="down")
    with patch("apps.api.health.probe_ollama", new=AsyncMock(return_value=offline)):
        with patch("apps.api.health.settings.use_fake_provider", False):
            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as client:
                res = await client.get("/health")
    assert res.status_code == 200
    body = res.json()
    assert body["backend"] is True
    assert "status" in body
    assert "models" in body
    assert body["ollama"] is False


@pytest.mark.asyncio
async def test_health_ok_alias_when_degraded() -> None:
    offline = OllamaProbeResult(reachable=False, installed_models=[])
    with patch("apps.api.health.probe_ollama", new=AsyncMock(return_value=offline)):
        with patch("apps.api.health.settings.use_fake_provider", False):
            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as client:
                body = (await client.get("/health")).json()
    assert body.get("ok") is True
    assert body["status"] == "degraded"
