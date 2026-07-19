"""Pipeline orchestrator with DeepSeek reasoning + Qwen writing.

Research → Trend Analysis → Insight Engine → Angle Finder → Strategist →
Writer → (Debate Mode) → Claim Checker → AI Writing Quality Analyzer →
Humanizer → Critic → Engagement Predictor
"""

from __future__ import annotations

import uuid
from typing import Any

from agents.angle_finder import AngleFinderAgent, AngleFinderInput
from agents.critic import CriticAgent, CriticInput
from agents.debate import DebateMode
from agents.engagement_predictor import EngagementPredictorAgent, EngagementPredictorInput
from agents.grounding import ClaimCheckerAgent, GroundingInput, check_claims
from agents.humanizer import HumanizerAgent, HumanizerInput
from agents.insight_engine import InsightEngineAgent, InsightEngineInput
from agents.memory_builder import approved_experience_texts, normalize_memory
from agents.researcher import ResearcherAgent, ResearcherInput
from agents.strategist import StrategistAgent, StrategistInput
from agents.trend_analyzer import TrendAnalyzerAgent, TrendAnalyzerInput
from agents.writer import WriterAgent, WriterInput
from agents.writing_quality import WritingQualityAnalyzer, WritingQualityInput
from apps.api.config import settings
from apps.api.providers import provider_for_stage
from models.base import ModelProvider
from models.router import RouterCallRecorder
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
    debate_mode: bool | None = None,
) -> dict[str, Any]:
    memory = normalize_memory(user_memory or load_user_memory())
    pipeline_run_id = uuid.uuid4()
    recorder = RouterCallRecorder()
    use_debate = settings.debate_mode if debate_mode is None else debate_mode

    def stage_provider(stage: str) -> ModelProvider:
        if provider is not None:
            return provider
        return provider_for_stage(stage, fake=fake, recorder=recorder)

    researcher = ResearcherAgent(stage_provider("researcher"))
    trend_analyzer = TrendAnalyzerAgent(stage_provider("trend_analyzer"))
    insight_engine = InsightEngineAgent(stage_provider("insight_engine"))
    angle_finder = AngleFinderAgent(stage_provider("angle_finder"))
    strategist = StrategistAgent(stage_provider("strategist"))
    writer = WriterAgent(stage_provider("writer"))
    claim_checker = ClaimCheckerAgent(stage_provider("claim_checker"))
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

    trends = await trend_analyzer.run(
        TrendAnalyzerInput(
            topic=topic,
            content_mode=content_mode,
            user_memory=memory,
            extra={
                "audience": audience,
                "research": research.data,
            },
        )
    )

    insight_out = await insight_engine.run(
        InsightEngineInput(
            topic=topic,
            content_mode=content_mode,
            user_memory=memory,
            extra={
                "audience": audience,
                "research": research.data,
                "trends": trends.data,
                "verified_experiences": approved_experience_texts(memory),
            },
        )
    )
    insight = insight_out.insight.as_dict()

    angles_out = await angle_finder.run(
        AngleFinderInput(
            topic=topic,
            content_mode=content_mode,
            user_memory=memory,
            extra={
                "audience": audience,
                "insight": insight,
                "trends": trends.data,
                "research": research.data,
            },
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
                "insight": insight,
                "trends": trends.data,
            },
        )
    )

    writer_extra = {
        "audience": audience,
        "angle": selected_angle,
        "strategy": strategy.data,
        "insight": insight,
    }
    written = await writer.run(
        WriterInput(
            topic=topic,
            content_mode=content_mode,
            format=format,
            user_memory=memory,
            extra=writer_extra,
        )
    )

    debate_payload: dict[str, Any] | None = None
    post_write_text = written.text
    if use_debate:
        debate = DebateMode(
            writer_provider=stage_provider("writer"),
            critic_provider=stage_provider("debate_critic"),
            rewrite_provider=stage_provider("debate_rewrite"),
        )
        debate_result = await debate.run(
            topic=topic,
            content_mode=content_mode,
            format=format,
            user_memory=memory,
            writer_extra=writer_extra,
            initial_draft=written.text,
        )
        debate_payload = debate_result.model_dump()
        post_write_text = debate_result.draft_v2 or written.text

    grounded = await claim_checker.run(
        GroundingInput(text=post_write_text, user_memory=memory, topic=topic)
    )

    quality = await quality_analyzer.run(
        WritingQualityInput(
            content=grounded.text or post_write_text,
            text=grounded.text or post_write_text,
            content_mode=content_mode,
            user_memory=memory,
            verified_memory=approved_experience_texts(memory),
        )
    )

    humanized = await humanizer.run(
        HumanizerInput(
            text=grounded.text or post_write_text,
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
    if debate_payload and debate_payload.get("generic_rejected"):
        approval_allowed = False
        safe = False

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
    if debate_payload and debate_payload.get("generic_rejected"):
        status = "rejected_generic"

    return {
        "pipeline_run_id": str(pipeline_run_id),
        "topic": topic,
        "content_mode": content_mode,
        "format": format,
        "audience": audience,
        "research": research.data,
        "trends": trends.data,
        "insight": insight_out.as_report(),
        "angles": angles,
        "selected_angle": selected_angle,
        "strategy": strategy.data,
        "draft": written.text,
        "debate": debate_payload,
        "grounded_draft": grounded.text,
        "final_text": final_text,
        "safe": safe,
        "approval_allowed": approval_allowed,
        "status": status,
        "model_routing": {
            "calls": list(recorder.calls),
            "deepseek_stages": recorder.stages_for_family("deepseek"),
            "qwen_stages": recorder.stages_for_family("qwen"),
        },
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
            "trend_analyzer": trends.model_dump(),
            "insight_engine": insight_out.model_dump(),
            "angle_finder": angles_out.model_dump(),
            "strategist": strategy.model_dump(),
            "writer": written.model_dump(),
            "debate": debate_payload,
            "claim_checker": grounded.model_dump(),
            "writing_quality": quality.model_dump(),
            "humanizer": humanized.model_dump(),
            "final_claim_checker": final_grounding.model_dump(),
            "final_writing_quality": final_quality.model_dump(),
            "critic": critiqued.model_dump(),
            "engagement_predictor": predicted.model_dump(),
        },
    }
