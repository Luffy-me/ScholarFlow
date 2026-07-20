"""Engagement estimator — probabilities + confidence interval + why."""

from __future__ import annotations

from agents.linkedin_optimizer._text import clamp01, has_question, jargon_density, normalize, word_count
from agents.linkedin_optimizer.schemas import (
    EngagementEstimate,
    HookOptimization,
    LinkedInPostScore,
    ReadabilityReport,
    StructureOptimization,
)


class EngagementEstimator:
    name = "engagement_estimator"

    def estimate(
        self,
        text: str,
        *,
        score: LinkedInPostScore | None = None,
        hook: HookOptimization | None = None,
        structure: StructureOptimization | None = None,
        readability: ReadabilityReport | None = None,
    ) -> EngagementEstimate:
        text = normalize(text)
        wc = word_count(text)
        why: list[str] = []

        hook_s = hook.scores.overall if hook else 0.4
        struct_s = structure.overall if structure else 0.4
        read_s = (readability.overall / 100.0) if readability else 0.5
        overall = (score.overall / 100.0) if score else mean_safe([hook_s, struct_s, read_s])

        save_p = clamp01(0.15 + 0.35 * overall + 0.25 * (score.practical_value / 100 if score else 0.4))
        if score and score.practical_value >= 80:
            why.append("High practical value increases save probability.")
        comment_p = clamp01(0.08 + 0.4 * (score.discussion_potential / 100 if score else 0.35) + (0.12 if has_question(text) else 0.0))
        if has_question(text):
            why.append("A question in the draft raises comment probability.")
        share_p = clamp01(0.05 + 0.3 * (score.novelty / 100 if score else hook_s) + 0.2 * (score.authority / 100 if score else 0.3))
        if score and score.novelty >= 75:
            why.append("Novelty supports share probability among practitioners.")
        follower_p = clamp01(0.04 + 0.25 * (score.authority / 100 if score else 0.3) + 0.2 * hook_s)
        if hook and hook.scores.stop_scroll >= 0.65:
            why.append("Strong stop-scroll hook supports follow probability.")
        read_through = clamp01(0.25 + 0.4 * read_s + 0.2 * struct_s - 0.15 * jargon_density(text))
        if 80 <= wc <= 240:
            read_through = clamp01(read_through + 0.08)
            why.append("Length sits in a read-through friendly band.")
        elif wc > 320:
            read_through = clamp01(read_through - 0.12)
            why.append("Long draft may reduce read-through on mobile.")

        center = mean_safe([save_p, comment_p, share_p, follower_p, read_through])
        # Wider interval when score missing / low evidence
        evidence = (score.evidence / 100.0) if score else 0.3
        half = 0.18 - 0.1 * evidence
        low = clamp01(center - half)
        high = clamp01(center + half)
        if not why:
            why.append("Estimates derived from hook, structure, readability, and LinkedIn score signals.")

        return EngagementEstimate(
            save_probability=round(save_p, 4),
            comment_probability=round(comment_p, 4),
            share_probability=round(share_p, 4),
            follower_probability=round(follower_p, 4),
            read_through_probability=round(read_through, 4),
            confidence_low=round(low, 4),
            confidence_high=round(high, 4),
            why=why,
        )


def mean_safe(values: list[float]) -> float:
    return sum(values) / len(values) if values else 0.0
