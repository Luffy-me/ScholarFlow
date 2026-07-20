"""Optimizer pipeline — runs AFTER content generation; max 2 optimization passes."""

from __future__ import annotations

from typing import Any

from agents.linkedin_optimizer.optimizer import LinkedInOptimizer
from agents.linkedin_optimizer.schemas import (
    MINIMUM_PUBLISH_SCORE,
    ImprovementSummary,
    OptimizationResult,
    OptimizerInput,
    OptimizerOutput,
)


class OptimizerPipeline:
    """
    Research → Reasoning → Writer → Claim Checker → Humanizer → Carousel Planner
      → LINKEDIN OPTIMIZER → Final Output

    This module owns only the optimizer stage. It does not replace Writer,
    Reasoning, Carousel, or Research agents.
    """

    name = "linkedin_optimizer_pipeline"
    max_passes = 2
    minimum_publish_score = MINIMUM_PUBLISH_SCORE

    def __init__(self, *, max_passes: int = 2) -> None:
        self.max_passes = max(1, min(2, int(max_passes)))
        self.optimizer = LinkedInOptimizer()

    def optimize(
        self,
        draft: str,
        *,
        evidence_refs: list[str] | None = None,
        user_memory: dict[str, Any] | None = None,
        reasoning_present: bool = False,
        carousel: Any | None = None,
        carousel_review: dict[str, Any] | None = None,
        content_mode: str = "founder",
    ) -> OptimizationResult:
        original = (draft or "").strip()
        if not original:
            empty = self.optimizer.analyzer.analyze("")
            empty.original_draft = ""
            empty.optimized_draft = ""
            empty.improvement_summary = ImprovementSummary(
                passes=0,
                pending=["No draft provided — optimizer does not write posts."],
                score_before=0,
                score_after=0,
                reached_threshold=False,
            )
            empty.meta = {"writes_posts": False, "error": "empty_draft"}
            return empty

        current = original
        applied_all: list[str] = []
        score_before = 0
        result: OptimizationResult | None = None
        passes_run = 0

        for pass_idx in range(1, self.max_passes + 1):
            result = self.optimizer.improve_once(
                current,
                evidence_refs=evidence_refs,
                user_memory=user_memory,
                reasoning_present=reasoning_present,
                carousel=carousel,
                carousel_review=carousel_review,
                content_mode=content_mode,
            )
            passes_run = pass_idx
            if pass_idx == 1:
                score_before = result.improvement_summary.score_before
            for item in result.improvement_summary.applied:
                applied_all.append(f"pass{pass_idx}: {item}")
            current = result.optimized_draft
            if result.linkedin_score.overall >= self.minimum_publish_score:
                break

        assert result is not None
        result.original_draft = original
        result.optimized_draft = current
        result.improvement_summary = ImprovementSummary(
            passes=passes_run,
            applied=applied_all,
            pending=result.improvement_summary.pending,
            score_before=score_before,
            score_after=result.linkedin_score.overall,
            reached_threshold=result.linkedin_score.overall >= self.minimum_publish_score,
        )
        result.meta = {
            **result.meta,
            "max_passes": self.max_passes,
            "pipeline_stage": "linkedin_optimizer",
            "after": ["writer", "claim_checker", "humanizer", "carousel_planner"],
            "writes_posts": False,
            "invents_facts": False,
            "preserves_author_intent": True,
            "minimum_publish_score": self.minimum_publish_score,
        }
        return result

    async def run(self, payload: OptimizerInput | dict[str, Any]) -> OptimizerOutput:
        if isinstance(payload, dict):
            text = str(payload.get("text") or "")
            extra = payload
            topic = str(payload.get("topic") or "")
            mode = str(payload.get("content_mode") or "founder")
            memory = payload.get("user_memory") or {}
        else:
            text = payload.text
            extra = payload.extra or {}
            topic = payload.topic
            mode = payload.content_mode or "founder"
            memory = payload.user_memory or {}

        result = self.optimize(
            text,
            evidence_refs=list(extra.get("evidence_refs") or []),
            user_memory=memory if isinstance(memory, dict) else {},
            reasoning_present=bool(extra.get("reasoning_present")),
            carousel=extra.get("carousel"),
            carousel_review=extra.get("carousel_review"),
            content_mode=mode,
        )
        summary_lines = [
            "LinkedIn Optimizer",
            f"Topic: {topic or '(from draft)'}",
            f"Score: {result.linkedin_score.overall}/{result.linkedin_score.minimum_publish_score}",
            f"Publish ready: {result.linkedin_score.publish_ready}",
            f"Passes: {result.improvement_summary.passes}",
        ]
        return OptimizerOutput(
            text="\n".join(summary_lines),
            result=result,
            data=result.as_dict(),
            meta={"agent": self.name, "writes_posts": False},
        )


# Public alias
LinkedInOptimizerPipeline = OptimizerPipeline
