"""Model capability vocabulary.

Agents declare required capabilities; the orchestrator selects providers.
No agent should import a concrete model provider.
"""

from __future__ import annotations

from enum import Enum


class Capability(str, Enum):
    REASONING = "reasoning"
    WRITING = "writing"
    CLASSIFICATION = "classification"
    SUMMARIZATION = "summarization"
    CRITIQUE = "critique"
    EXTRACTION = "extraction"
    RANKING = "ranking"
    RESEARCH = "research"
    TREND_DETECTION = "trend_detection"


# Default family preferences per capability (not hardcoded model IDs).
CAPABILITY_FAMILY_PREFERENCE: dict[Capability, tuple[str, ...]] = {
    Capability.REASONING: ("deepseek", "qwen"),
    Capability.WRITING: ("qwen", "deepseek"),
    Capability.CLASSIFICATION: ("qwen", "deepseek"),
    Capability.SUMMARIZATION: ("qwen", "deepseek"),
    Capability.CRITIQUE: ("deepseek", "qwen"),
    Capability.EXTRACTION: ("deepseek", "qwen"),
    Capability.RANKING: ("deepseek", "qwen"),
    Capability.RESEARCH: ("deepseek", "qwen"),
    Capability.TREND_DETECTION: ("deepseek", "qwen"),
}


# Stage → primary capability (used when pipeline still names stages).
STAGE_CAPABILITIES: dict[str, Capability] = {
    "researcher": Capability.RESEARCH,
    "research_agent": Capability.RESEARCH,
    "research": Capability.RESEARCH,
    "trend_analyzer": Capability.TREND_DETECTION,
    "trend_analysis": Capability.TREND_DETECTION,
    "insight_engine": Capability.REASONING,
    "insight": Capability.REASONING,
    "angle_finder": Capability.REASONING,
    "strategist": Capability.REASONING,
    "writer": Capability.WRITING,
    "humanizer": Capability.WRITING,
    "debate_rewrite": Capability.WRITING,
    "claim_checker": Capability.EXTRACTION,
    "grounding": Capability.EXTRACTION,
    "writing_quality": Capability.CRITIQUE,
    "critic": Capability.CRITIQUE,
    "debate_critic": Capability.CRITIQUE,
    "debate_final": Capability.CRITIQUE,
    "engagement_predictor": Capability.RANKING,
    "predictor": Capability.RANKING,
    "research_summarizer": Capability.SUMMARIZATION,
    "research_extractor": Capability.EXTRACTION,
    "research_ranker": Capability.RANKING,
    "content_opportunity": Capability.RANKING,
    "quality_scorer": Capability.RANKING,
}
