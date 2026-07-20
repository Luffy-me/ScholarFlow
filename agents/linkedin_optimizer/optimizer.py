"""LinkedIn Optimizer — improves an existing draft; never writes a new post."""

from __future__ import annotations

from typing import Any

from agents.linkedin_optimizer._text import (
    normalize,
    preserve_body_after_hook,
    strip_trailing_hashtag_soup,
)
from agents.linkedin_optimizer.cta_optimizer import CTAOptimizer
from agents.linkedin_optimizer.hook_optimizer import HookOptimizer
from agents.linkedin_optimizer.quality_analyzer import QualityAnalyzer
from agents.linkedin_optimizer.schemas import (
    MINIMUM_PUBLISH_SCORE,
    ImprovementSummary,
    OptimizationResult,
)
from agents.linkedin_optimizer.structure_optimizer import StructureOptimizer


class LinkedInOptimizer:
    """Single optimization pass over an existing draft."""

    name = "linkedin_optimizer"
    minimum_publish_score = MINIMUM_PUBLISH_SCORE

    def __init__(self) -> None:
        self.analyzer = QualityAnalyzer()
        self.hooks = HookOptimizer()
        self.structure = StructureOptimizer()
        self.cta = CTAOptimizer()

    def improve_once(
        self,
        text: str,
        *,
        evidence_refs: list[str] | None = None,
        user_memory: dict[str, Any] | None = None,
        reasoning_present: bool = False,
        carousel: Any | None = None,
        carousel_review: dict[str, Any] | None = None,
        content_mode: str = "founder",
        apply_hook: bool = True,
        apply_structure: bool = True,
        apply_cta: bool = True,
    ) -> OptimizationResult:
        original = normalize(text)
        report = self.analyzer.analyze(
            original,
            evidence_refs=evidence_refs,
            user_memory=user_memory,
            reasoning_present=reasoning_present,
            carousel=carousel,
            carousel_review=carousel_review,
            content_mode=content_mode,
        )
        draft = original
        applied: list[str] = []

        # 1) Safe cleanup (no fact changes)
        cleaned = strip_trailing_hashtag_soup(draft)
        if cleaned != draft:
            draft = cleaned
            applied.append("Removed trailing hashtag soup.")

        # 2) Hook alternative if materially better (reuses existing content)
        if apply_hook and report.hook.alternatives:
            best = report.hook.alternatives[0]
            if best.scores.overall > report.hook.scores.overall + 0.03:
                draft = preserve_body_after_hook(draft, best.text)
                applied.append(f"Applied ranked hook alternative #{best.rank}.")
                report.hook.selected = best.text

        # 3) Structure whitespace only
        if apply_structure and report.structure.whitespace < 0.7:
            structured = self.structure.apply_safe_structure(draft)
            if structured != draft:
                draft = structured
                applied.append("Improved paragraph whitespace for scanning.")

        # 4) CTA append (optional ask — does not alter claims)
        if apply_cta:
            cta = self.cta.recommend(draft, score=report.linkedin_score)
            updated = self.cta.apply(draft, cta)
            if updated != draft:
                draft = updated
                applied.append(f"Applied {cta.chosen} CTA.")
            report.cta = cta

        # Re-analyze optimized draft
        final = self.analyzer.analyze(
            draft,
            evidence_refs=evidence_refs,
            user_memory=user_memory,
            reasoning_present=reasoning_present,
            carousel=carousel,
            carousel_review=carousel_review,
            content_mode=content_mode,
        )
        final.original_draft = original
        final.optimized_draft = draft
        final.improvement_summary = ImprovementSummary(
            passes=1,
            applied=applied,
            pending=[r for r in final.recommendations if r not in applied][:8],
            score_before=report.linkedin_score.overall,
            score_after=final.linkedin_score.overall,
            reached_threshold=final.linkedin_score.publish_ready,
        )
        final.meta = {
            "writes_posts": False,
            "preserves_author_intent": True,
            "invents_facts": False,
            "minimum_publish_score": self.minimum_publish_score,
        }
        return final
