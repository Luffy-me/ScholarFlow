"""Pipeline orchestrator with writing-quality intelligence.

Research → Angle Finder → Strategist → Writer → Claim Checker →
AI Writing Quality Analyzer → Humanizer → Critic → Engagement Predictor
"""

from __future__ import annotations

import uuid
from typing import Any

from agents.angle_finder import AngleFinderAgent, AngleFinderInput
from agents.critic import CriticAgent, CriticInput
from agents.engagement_predictor import EngagementPredictorAgent, EngagementPredictorInput
from agents.grounding import ClaimCheckerAgent, GroundingInput, check_claims
from agents.humanizer import HumanizerAgent, HumanizerInput
from agents.memory_builder import normalize_memory, approved_experience_texts
from agents.researcher import ResearcherAgent, ResearcherInput
from agents.strategist import StrategistAgent, StrategistInput
from agents.writer import WriterAgent, WriterInput
from agents.writing_quality import WritingQualityAnalyzer, WritingQualityInput
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
    selected_angle_index: int = 0,
) -> dict[str, Any]:
    memory = normalize_memory(user_memory or load_user_memory())
    pipeline_run_id = uuid.uuid4()

    def stage_provider(stage: str) -> ModelProvider:
        if provider is not None:
            return provider
        return provider_for_stage(stage, fake=fake)

    researcher = ResearcherAgent(stage_provider("researcher"))
    angle_finder = AngleFinderAgent(stage_provider("angle_finder"))
    strategist = StrategistAgent(stage_provider("strategist"))
    writer = WriterAgent(stage_provider("writer"))
    claim_checker = ClaimCheckerAgent(build_base_provider(fake=True))
    quality_analyzer = WritingQualityAnalyzer(stage_provider("writing_quality"))
    humanizer = HumanizerAgent(stage_provider("humanizer"))
    critic = CriticAgent(stage_provider("critic"))
    predictor = EngagementPredictorAgent(stage_provider("predictor"))

    research = await researcher.run(
        ResearcherInput(
            topic=topic,
            content_mode=content_mode,
            user_memory=memory,
            extra={"audience": audience} if audience else {},
        )
    )

    angles_out = await angle_finder.run(
        AngleFinderInput(
            topic=topic,
            content_mode=content_mode,
            user_memory=memory,
            extra={"audience": audience} if audience else {},
        )
    )
    angles = [a.model_dump() for a in angles_out.angles]
    if not angles:
        raise RuntimeError("Angle finder returned no angles")
    idx = max(0, min(selected_angle_index, len(angles) - 1))
    selected_angle = angles[idx]

    strategy = await strategist.run(
        StrategistInput(
            topic=topic,
            content_mode=content_mode,
            user_memory=memory,
            extra={
                "audience": audience,
                "angle": selected_angle,
                "research": research.data,
            },
        )
    )

    written = await writer.run(
        WriterInput(
            topic=topic,
            content_mode=content_mode,
            format=format,
            user_memory=memory,
            extra={
                "audience": audience,
                "angle": selected_angle,
                "strategy": strategy.data,
            },
        )
    )

    grounded = await claim_checker.run(
        GroundingInput(text=written.text, user_memory=memory, topic=topic)
    )

    quality = await quality_analyzer.run(
        WritingQualityInput(
            content=grounded.text or written.text,
            text=grounded.text or written.text,
            content_mode=content_mode,
            user_memory=memory,
            verified_memory=approved_experience_texts(memory),
        )
    )

    humanized = await humanizer.run(
        HumanizerInput(
            text=grounded.text or written.text,
            user_memory=memory,
            topic=topic,
            extra={"improvements": quality.improvements, "writing_quality": quality.as_report()},
        )
    )

    final_grounding = await claim_checker.run(
        GroundingInput(text=humanized.text, user_memory=memory, topic=topic)
    )
    final_text = final_grounding.text if final_grounding.safe or final_grounding.text else humanized.text
    if not final_grounding.safe and final_grounding.text:
        final_text = final_grounding.text
        final_grounding = await claim_checker.run(
            GroundingInput(text=final_text, user_memory=memory, topic=topic)
        )

    final_check = check_claims(final_text, memory)
    safe = final_check.safe
    approval_allowed = safe

    final_quality = await quality_analyzer.run(
        WritingQualityInput(
            content=final_text,
            text=final_text,
            content_mode=content_mode,
            user_memory=memory,
            verified_memory=approved_experience_texts(memory),
        )
    )

    critiqued = await critic.run(
        CriticInput(
            text=final_text,
            user_memory=memory,
            content_mode=content_mode,
            extra={"writing_quality": final_quality.as_report()},
        )
    )
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
        "research": research.data,
        "angles": angles,
        "selected_angle": selected_angle,
        "strategy": strategy.data,
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
        "writing_quality": final_quality.as_report(),
        "critic": {
            "scores": critiqued.scores.model_dump(),
            "issues": critiqued.issues,
        },
        "engagement_prediction": predicted.scores.model_dump(),
        "stages": {
            "researcher": research.model_dump(),
            "angle_finder": angles_out.model_dump(),
            "strategist": strategy.model_dump(),
            "writer": written.model_dump(),
            "claim_checker": grounded.model_dump(),
            "writing_quality": quality.model_dump(),
            "humanizer": humanized.model_dump(),
            "final_claim_checker": final_grounding.model_dump(),
            "final_writing_quality": final_quality.model_dump(),
            "critic": critiqued.model_dump(),
            "engagement_predictor": predicted.model_dump(),
        },
    }
