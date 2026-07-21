"""Shared httpx client settings for Ollama (no proxy env leakage)."""

from __future__ import annotations

import httpx


def ollama_timeout(*, connect: float = 5.0, read: float = 300.0) -> httpx.Timeout:
    return httpx.Timeout(connect=connect, read=read, write=30.0, pool=connect)


def ollama_client(*, timeout: httpx.Timeout | float) -> httpx.AsyncClient:
    if isinstance(timeout, (int, float)):
        timeout = httpx.Timeout(timeout)
    return httpx.AsyncClient(timeout=timeout, trust_env=False)
