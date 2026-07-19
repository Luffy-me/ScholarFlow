"""Pipeline orchestrator with Truth Layer v2 grounding.

Writer → Claim Checker → Humanizer → Critic → Engagement Predictor
"""

from __future__ import annotations

import uuid
from typing import Any

from agents.critic import CriticAgent, CriticInput
from agents.engagement_predictor import EngagementPredictorAgent, EngagementPredictorInput
from agents.grounding import ClaimCheckerAgent, GroundingInput, check_claims
from agents.humanizer import HumanizerAgent, HumanizerInput
from agents.writer import WriterAgent, WriterInput
from apps.api.providers import build_base_provider, provider_for_stage
from models.base import ModelProvider
from shared.knowledge import load_user_memory


async def run_generation_pipeline(
    provider: ModelProvider | None = None,
    *,
    topic: str,
    content_mode: str = "founder",
    format: str = "short",
    audience: str = "",
    user_memory: dict[str, Any] | None = None,
    fake: bool = False,
) -> dict[str, Any]:
    memory = user_memory or load_user_memory()
    pipeline_run_id = uuid.uuid4()

    # Per-stage model routing (falls back to a shared provider when FakeProvider is used).
    writer_provider = provider_for_stage("writer", fake=fake) if provider is None else provider
    humanizer_provider = provider_for_stage("humanizer", fake=fake) if provider is None else provider
    critic_provider = provider_for_stage("critic", fake=fake) if provider is None else provider
    predictor_provider = provider_for_stage("predictor", fake=fake) if provider is None else provider

    # If caller passed an explicit provider (tests), use it for all LLM stages.
    if provider is not None:
        writer_provider = humanizer_provider = critic_provider = predictor_provider = provider

    writer = WriterAgent(writer_provider)
    claim_checker = ClaimCheckerAgent(build_base_provider(fake=True))
    humanizer = HumanizerAgent(humanizer_provider)
    critic = CriticAgent(critic_provider)
    predictor = EngagementPredictorAgent(predictor_provider)

    written = await writer.run(
        WriterInput(
            topic=topic,
            content_mode=content_mode,
            format=format,
            user_memory=memory,
            extra={"audience": audience} if audience else {},
        )
    )

    # Truth Layer v2 — sanitize ungrounded first-person claims before humanizing.
    grounded = await claim_checker.run(
        GroundingInput(text=written.text, user_memory=memory, topic=topic)
    )

    humanized = await humanizer.run(
        HumanizerInput(text=grounded.text or written.text, user_memory=memory, topic=topic)
    )

    # Re-check after humanizer (must not re-introduce unsupported claims).
    final_grounding = await claim_checker.run(
        GroundingInput(text=humanized.text, user_memory=memory, topic=topic)
    )
    # If humanizer reintroduced claims, keep sanitized version.
    final_text = final_grounding.text if final_grounding.safe or final_grounding.text else humanized.text
    if not final_grounding.safe and final_grounding.text:
        final_text = final_grounding.text
        final_grounding = await claim_checker.run(
            GroundingInput(text=final_text, user_memory=memory, topic=topic)
        )

    final_check = check_claims(final_text, memory)
    safe = final_check.safe
    approval_allowed = safe

    critiqued = await critic.run(CriticInput(text=final_text, user_memory=memory))
    predicted = await predictor.run(
        EngagementPredictorInput(text=final_text, user_memory=memory)
    )

    status = "reviewed" if approval_allowed else "unsafe"

    return {
        "pipeline_run_id": str(pipeline_run_id),
        "topic": topic,
        "content_mode": content_mode,
        "format": format,
        "audience": audience,
        "draft": written.text,
        "grounded_draft": grounded.text,
        "final_text": final_text,
        "safe": safe,
        "approval_allowed": approval_allowed,
        "status": status,
        "grounding": {
            "approved_claims": [c.model_dump() for c in final_check.approved_claims],
            "rejected_claims": [c.model_dump() for c in final_check.rejected_claims]
            + list(grounded.rejected_claims),
            "warnings": list(dict.fromkeys(final_check.warnings + grounded.warnings)),
        },
        "critic": {
            "scores": critiqued.scores.model_dump(),
            "issues": critiqued.issues,
        },
        "engagement_prediction": predicted.scores.model_dump(),
        "stages": {
            "writer": written.model_dump(),
            "claim_checker": grounded.model_dump(),
            "humanizer": humanized.model_dump(),
            "final_claim_checker": final_grounding.model_dump(),
            "critic": critiqued.model_dump(),
            "engagement_predictor": predicted.model_dump(),
        },
    }
