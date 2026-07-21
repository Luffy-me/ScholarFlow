"""Pipeline stage logging wrapper."""

from __future__ import annotations

import logging
from collections.abc import Awaitable
from typing import TypeVar

from apps.api.pipeline_errors import PipelineStageError

logger = logging.getLogger("scholarflow.pipeline")

T = TypeVar("T")


async def run_stage(stage: str, coro: Awaitable[T]) -> T:
    logger.info("[%s] started", stage)
    try:
        result = await coro
    except PipelineStageError:
        raise
    except Exception as exc:  # noqa: BLE001
        logger.error("[%s] failed: %s", stage, exc)
        raise PipelineStageError(stage, str(exc)) from exc
    logger.info("[%s] completed", stage)
    return result
