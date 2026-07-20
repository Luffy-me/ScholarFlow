"""Structured API errors (no tracebacks to clients)."""

from __future__ import annotations

import logging
from typing import Any

from fastapi import Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from models.ollama import OllamaUnavailableError

logger = logging.getLogger(__name__)


def _structured(
    *,
    error: str,
    message: str,
    resolution: str | None = None,
    status_code: int = 400,
    extra: dict[str, Any] | None = None,
) -> JSONResponse:
    body: dict[str, Any] = {"error": error, "message": message}
    if resolution:
        body["resolution"] = resolution
    if extra:
        body.update(extra)
    return JSONResponse(status_code=status_code, content=body)


def register_exception_handlers(app) -> None:
    @app.exception_handler(OllamaUnavailableError)
    async def _ollama_unavailable(_request: Request, exc: OllamaUnavailableError) -> JSONResponse:
        text = str(exc)
        resolution = None
        if "ollama pull" in text.lower():
            resolution = text.split("Run:")[-1].strip() if "Run:" in text else text
        elif "not reachable" in text.lower() or "unavailable" in text.lower():
            resolution = "Run: ollama serve"
        return _structured(
            error="OllamaUnavailable",
            message=text,
            resolution=resolution or "Ensure Ollama is running and required models are pulled.",
            status_code=503,
        )

    @app.exception_handler(StarletteHTTPException)
    async def _http_exception(_request: Request, exc: StarletteHTTPException) -> JSONResponse:
        detail = exc.detail
        if isinstance(detail, dict) and "error" in detail:
            return JSONResponse(status_code=exc.status_code, content=detail)
        if isinstance(detail, dict):
            return _structured(
                error="RequestError",
                message=str(detail.get("message") or detail),
                status_code=exc.status_code,
                extra={k: v for k, v in detail.items() if k != "message"},
            )
        return _structured(
            error="RequestError",
            message=str(detail),
            status_code=exc.status_code,
        )

    @app.exception_handler(RequestValidationError)
    async def _validation(_request: Request, exc: RequestValidationError) -> JSONResponse:
        return _structured(
            error="ValidationError",
            message="Request validation failed.",
            status_code=422,
            extra={"issues": exc.errors()},
        )

    @app.exception_handler(Exception)
    async def _unhandled(_request: Request, exc: Exception) -> JSONResponse:
        logger.exception("Unhandled API error: %s", exc)
        return _structured(
            error="InternalError",
            message="An unexpected error occurred.",
            resolution="Check API logs on the server.",
            status_code=500,
        )
