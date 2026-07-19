"""Rewrite loop — iterate until quality score >= threshold or max iterations."""

from __future__ import annotations

from typing import Any, Awaitable, Callable

from agents.quality.scorer import QualityScore, QualityScorer
from models.capabilities import Capability


RewriteFn = Callable[[str, list[str]], Awaitable[str]]


class RewriteLoop:
    name = "rewrite_loop"
    capabilities = [Capability.CRITIQUE, Capability.WRITING]

    def __init__(
        self,
        *,
        scorer: QualityScorer | None = None,
        threshold: int = 90,
        max_iterations: int = 3,
    ) -> None:
        self.scorer = scorer or QualityScorer()
        self.threshold = threshold
        self.max_iterations = max_iterations

    async def run(
        self,
        text: str,
        *,
        rewrite: RewriteFn,
        user_memory: dict[str, Any] | None = None,
        safe: bool = True,
        engagement_overall: int | None = None,
        insight_originality: int | None = None,
    ) -> dict[str, Any]:
        current = text
        history: list[dict[str, Any]] = []
        score = self.scorer.score(
            current,
            user_memory=user_memory,
            safe=safe,
            engagement_overall=engagement_overall,
            insight_originality=insight_originality,
        )
        history.append({"iteration": 0, "score": score.as_dict(), "text": current})

        iteration = 0
        while score.overall < self.threshold and iteration < self.max_iterations:
            iteration += 1
            improvements = self._improvements(score)
            current = await rewrite(current, improvements)
            score = self.scorer.score(
                current,
                user_memory=user_memory,
                safe=safe,
                engagement_overall=engagement_overall,
                insight_originality=insight_originality,
            )
            history.append({"iteration": iteration, "score": score.as_dict(), "text": current})

        return {
            "text": current,
            "score": score.as_dict(),
            "iterations": iteration,
            "reached_threshold": score.overall >= self.threshold,
            "history": history,
        }

    def _improvements(self, score: QualityScore) -> list[str]:
        tips: list[str] = []
        if score.truth < 70:
            tips.append("Remove unverified claims; keep only grounded facts.")
        if score.specificity < 70:
            tips.append("Add one concrete tool, experiment, or constraint.")
        if score.human_voice < 70:
            tips.append("Use first-person observation without inventing experiences.")
        if score.originality < 70:
            tips.append("Replace generic statements with a contrarian or hidden pattern.")
        if score.details.get("generic_ai"):
            tips.append("Delete generic openings and buzzwords.")
        if not tips:
            tips.append("Tighten clarity and end with a discussion question.")
        return tips
