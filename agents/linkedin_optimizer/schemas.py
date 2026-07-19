"""Schemas for the LinkedIn Optimization Layer (post-generation only)."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field

from agents.base import AgentInput, AgentOutput

MINIMUM_PUBLISH_SCORE = 95


class HookScores(BaseModel):
    curiosity: float = 0.0
    specificity: float = 0.0
    novelty: float = 0.0
    authority: float = 0.0
    stop_scroll: float = 0.0
    overall: float = 0.0


class HookAlternative(BaseModel):
    rank: int = 0
    text: str
    scores: HookScores = Field(default_factory=HookScores)
    rationale: str = ""


class HookOptimization(BaseModel):
    first_two_lines: str = ""
    first_sentence: str = ""
    scores: HookScores = Field(default_factory=HookScores)
    alternatives: list[HookAlternative] = Field(default_factory=list)
    selected: str = ""
    recommendations: list[str] = Field(default_factory=list)


class StructureOptimization(BaseModel):
    paragraph_rhythm: float = 0.0
    story_flow: float = 0.0
    sentence_variety: float = 0.0
    whitespace: float = 0.0
    transitions: float = 0.0
    scanning: float = 0.0
    overall: float = 0.0
    recommendations: list[str] = Field(default_factory=list)


class EngagementEstimate(BaseModel):
    save_probability: float = 0.0
    comment_probability: float = 0.0
    share_probability: float = 0.0
    follower_probability: float = 0.0
    read_through_probability: float = 0.0
    confidence_low: float = 0.0
    confidence_high: float = 0.0
    why: list[str] = Field(default_factory=list)


class ReadabilityReport(BaseModel):
    avg_sentence_length: float = 0.0
    avg_paragraph_length: float = 0.0
    reading_speed_wpm: float = 220.0
    estimated_read_seconds: float = 0.0
    jargon_density: float = 0.0
    formatting_quality: float = 0.0
    overall: float = 0.0
    recommendations: list[str] = Field(default_factory=list)


class CTARecommendation(BaseModel):
    discussion_cta: str = ""
    save_cta: str = ""
    follow_cta: str = ""
    chosen: str = "no_cta"  # discussion | save | follow | no_cta
    chosen_text: str = ""
    rationale: str = ""


class CarouselReviewReport(BaseModel):
    slide_density: float = 0.0
    visual_hierarchy: float = 0.0
    narrative_flow: float = 0.0
    information_load: float = 0.0
    transitions: float = 0.0
    consistency: float = 0.0
    overall: float = 0.0
    recommendations: list[str] = Field(default_factory=list)
    slide_count: int = 0


class PublishingRecommendations(BaseModel):
    best_posting_day: str = ""
    best_posting_window: str = ""
    hashtags_help: bool = False
    hashtag_note: str = ""
    ideal_post_length_words: tuple[int, int] = (120, 220)
    ideal_carousel_length_slides: tuple[int, int] = (6, 10)
    notes: list[str] = Field(default_factory=list)


class LinkedInPostScore(BaseModel):
    hook: int = 0
    novelty: int = 0
    evidence: int = 0
    reasoning: int = 0
    originality: int = 0
    readability: int = 0
    authority: int = 0
    practical_value: int = 0
    discussion_potential: int = 0
    overall: int = 0
    minimum_publish_score: int = MINIMUM_PUBLISH_SCORE
    publish_ready: bool = False
    dimensions: dict[str, int] = Field(default_factory=dict)

    def as_dict(self) -> dict[str, Any]:
        return self.model_dump()


class ImprovementSummary(BaseModel):
    passes: int = 0
    applied: list[str] = Field(default_factory=list)
    pending: list[str] = Field(default_factory=list)
    score_before: int = 0
    score_after: int = 0
    reached_threshold: bool = False


class OptimizationResult(BaseModel):
    original_draft: str = ""
    optimized_draft: str = ""
    improvement_summary: ImprovementSummary = Field(default_factory=ImprovementSummary)
    linkedin_score: LinkedInPostScore = Field(default_factory=LinkedInPostScore)
    predicted_engagement: EngagementEstimate = Field(default_factory=EngagementEstimate)
    publishing_recommendations: PublishingRecommendations = Field(
        default_factory=PublishingRecommendations
    )
    hook: HookOptimization = Field(default_factory=HookOptimization)
    structure: StructureOptimization = Field(default_factory=StructureOptimization)
    readability: ReadabilityReport = Field(default_factory=ReadabilityReport)
    cta: CTARecommendation = Field(default_factory=CTARecommendation)
    carousel: CarouselReviewReport = Field(default_factory=CarouselReviewReport)
    recommendations: list[str] = Field(default_factory=list)
    meta: dict[str, Any] = Field(default_factory=dict)

    def as_dict(self) -> dict[str, Any]:
        return self.model_dump()


class OptimizerInput(AgentInput):
    """Existing draft (+ optional carousel / evidence context). Never a blank slate."""

    pass


class OptimizerOutput(AgentOutput):
    result: OptimizationResult = Field(default_factory=OptimizationResult)

    def as_report(self) -> dict[str, Any]:
        return self.result.as_dict()
