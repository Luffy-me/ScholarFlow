"""Pipeline orchestrator: writer → humanizer → critic → engagement predictor."""

from __future__ import annotations

import uuid
from typing import Any

from agents.critic import CriticAgent, CriticInput
from agents.engagement_predictor import EngagementPredictorAgent, EngagementPredictorInput
from agents.humanizer import HumanizerAgent, HumanizerInput
from agents.writer import WriterAgent, WriterInput
from models.base import ModelProvider
from shared.knowledge import load_user_memory


async def run_generation_pipeline(
    provider: ModelProvider,
    *,
    topic: str,
    content_mode: str = "founder",
    format: str = "short",
    audience: str = "",
    user_memory: dict[str, Any] | None = None,
) -> dict[str, Any]:
    memory = user_memory or load_user_memory()
    pipeline_run_id = uuid.uuid4()

    writer = WriterAgent(provider)
    humanizer = HumanizerAgent(provider)
    critic = CriticAgent(provider)
    predictor = EngagementPredictorAgent(provider)

    written = await writer.run(
        WriterInput(
            topic=topic,
            content_mode=content_mode,
            format=format,
            user_memory=memory,
            extra={"audience": audience} if audience else {},
        )
    )
    humanized = await humanizer.run(HumanizerInput(text=written.text, user_memory=memory))
    critiqued = await critic.run(CriticInput(text=humanized.text, user_memory=memory))
    predicted = await predictor.run(
        EngagementPredictorInput(text=humanized.text, user_memory=memory)
    )

    return {
        "pipeline_run_id": str(pipeline_run_id),
        "topic": topic,
        "content_mode": content_mode,
        "format": format,
        "audience": audience,
        "draft": written.text,
        "final_text": humanized.text,
        "critic": {
            "scores": critiqued.scores.model_dump(),
            "issues": critiqued.issues,
        },
        "engagement_prediction": predicted.scores.model_dump(),
        "stages": {
            "writer": written.model_dump(),
            "humanizer": humanized.model_dump(),
            "critic": critiqued.model_dump(),
            "engagement_predictor": predicted.model_dump(),
        },
    }
