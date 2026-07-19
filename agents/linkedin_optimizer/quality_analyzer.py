"""Quality analyzer — aggregate LinkedIn optimization diagnostics (not a writer)."""

from __future__ import annotations

from typing import Any

from agents.linkedin_optimizer.cta_optimizer import CTAOptimizer
from agents.linkedin_optimizer.engagement_estimator import EngagementEstimator
from agents.linkedin_optimizer.hook_optimizer import HookOptimizer
from agents.linkedin_optimizer.post_score import PostScoreEngine
from agents.linkedin_optimizer.readability_optimizer import ReadabilityOptimizer
from agents.linkedin_optimizer.schemas import OptimizationResult
from agents.linkedin_optimizer.structure_optimizer import StructureOptimizer
from agents.linkedin_optimizer.carousel_reviewer import CarouselReviewer
from agents.linkedin_optimizer.publishing_recommendations import PublishingAdvisor


class QualityAnalyzer:
    """Run all analyzers on an existing draft and return a structured report."""

    name = "linkedin_quality_analyzer"

    def __init__(self) -> None:
        self.hooks = HookOptimizer()
        self.structure = StructureOptimizer()
        self.readability = ReadabilityOptimizer()
        self.cta = CTAOptimizer()
        self.scorer = PostScoreEngine()
        self.engagement = EngagementEstimator()
        self.carousel = CarouselReviewer()
        self.publishing = PublishingAdvisor()

    def analyze(
        self,
        text: str,
        *,
        evidence_refs: list[str] | None = None,
        user_memory: dict[str, Any] | None = None,
        reasoning_present: bool = False,
        carousel: Any | None = None,
        carousel_review: dict[str, Any] | None = None,
        content_mode: str = "founder",
    ) -> OptimizationResult:
        hook = self.hooks.optimize(text)
        structure = self.structure.analyze(text)
        readability = self.readability.analyze(text)
        score = self.scorer.score(
            text,
            hook=hook,
            structure=structure,
            readability=readability,
            evidence_refs=evidence_refs,
            user_memory=user_memory,
            reasoning_present=reasoning_present,
        )
        cta = self.cta.recommend(text, score=score)
        engagement = self.engagement.estimate(
            text, score=score, hook=hook, structure=structure, readability=readability
        )
        carousel_report = self.carousel.review(carousel, existing_review=carousel_review)
        publishing = self.publishing.recommend(
            text, score=score, carousel=carousel_report, content_mode=content_mode
        )
        recommendations = (
            list(hook.recommendations)
            + list(structure.recommendations)
            + list(readability.recommendations)
            + list(carousel_report.recommendations)
            + [cta.rationale]
            + list(publishing.notes)
        )
        return OptimizationResult(
            original_draft=text,
            optimized_draft=text,
            linkedin_score=score,
            predicted_engagement=engagement,
            publishing_recommendations=publishing,
            hook=hook,
            structure=structure,
            readability=readability,
            cta=cta,
            carousel=carousel_report,
            recommendations=[r for r in recommendations if r],
            meta={"phase": "analyze", "writes_posts": False},
        )
