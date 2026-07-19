"""LinkedIn post score — multi-dimension score with publish threshold 95."""

from __future__ import annotations

import re
from typing import Any

from agents.linkedin_optimizer._text import clamp100, has_question, normalize, word_count
from agents.linkedin_optimizer.schemas import (
    MINIMUM_PUBLISH_SCORE,
    HookOptimization,
    LinkedInPostScore,
    ReadabilityReport,
    StructureOptimization,
)
from shared.quality import scan_text


class PostScoreEngine:
    name = "post_score"
    minimum_publish_score = MINIMUM_PUBLISH_SCORE

    def score(
        self,
        text: str,
        *,
        hook: HookOptimization | None = None,
        structure: StructureOptimization | None = None,
        readability: ReadabilityReport | None = None,
        evidence_refs: list[str] | None = None,
        user_memory: dict[str, Any] | None = None,
        reasoning_present: bool = False,
    ) -> LinkedInPostScore:
        text = normalize(text)
        scan = scan_text(text, user_memory)
        evidence_refs = evidence_refs or []

        hook_score = clamp100((hook.scores.overall if hook else 0.4) * 100)
        if scan.has_weak_hook:
            hook_score = min(hook_score, 45)

        novelty = clamp100((hook.scores.novelty if hook else 0.35) * 100)
        if any(k in text.lower() for k in ("overlooked", "counterintuitive", "most teams", "instead")):
            novelty = max(novelty, 70)

        evidence = 40
        if evidence_refs:
            evidence = min(95, 55 + 8 * min(5, len(evidence_refs)))
        fabricated_scale = bool(
            re.search(r"\b(\d+\s*(million|billion)|10x|100x)\b", text, re.I)
        ) and not evidence_refs
        if scan.has_fake_experience or fabricated_scale:
            evidence = min(evidence, 20)

        reasoning = 55 if reasoning_present else 40
        if any(k in text.lower() for k in ("because", "trade-off", "tradeoff", "constraint", "if ")):
            reasoning = max(reasoning, 70)
        if "however" in text.lower() or "instead" in text.lower():
            reasoning = max(reasoning, 75)

        originality = clamp100(60 + (10 if novelty >= 70 else 0) - (25 if scan.has_generic_ai else 0))
        readability_score = readability.overall if readability else 55
        authority = clamp100((hook.scores.authority if hook else 0.3) * 100)
        if evidence_refs:
            authority = max(authority, 65)
        if scan.has_fake_experience:
            authority = min(authority, 25)

        practical = 50
        if any(k in text.lower() for k in ("playbook", "checklist", "framework", "step", "metric", "measure")):
            practical = 80
        if word_count(text) >= 80:
            practical = max(practical, 60)

        discussion = 45
        if has_question(text):
            discussion = 78
        if any(k in text.lower() for k in ("agree", "disagree", "what would you", "comment")):
            discussion = max(discussion, 72)
        if structure and structure.overall >= 0.7:
            discussion = max(discussion, 60)

        dims = {
            "hook": hook_score,
            "novelty": novelty,
            "evidence": evidence,
            "reasoning": reasoning,
            "originality": originality,
            "readability": readability_score,
            "authority": authority,
            "practical_value": practical,
            "discussion_potential": discussion,
        }
        base = sum(dims.values()) / len(dims)
        # Excellence bonus so strong, evidence-backed posts can clear publish threshold 95
        high_dims = sum(1 for v in dims.values() if v >= 72)
        bonus = 0.0
        if high_dims >= 7:
            bonus += 12
        if high_dims >= 8:
            bonus += 6
        if evidence_refs and evidence >= 70 and not scan.has_fake_experience:
            bonus += 5
        if hook_score >= 75 and readability_score >= 75 and reasoning >= 70:
            bonus += 5
        overall = clamp100(base + bonus)
        # Hard gates
        if scan.has_fake_experience or fabricated_scale:
            overall = min(overall, 40)
        if scan.has_generic_ai:
            overall = min(overall, 70)

        return LinkedInPostScore(
            hook=hook_score,
            novelty=novelty,
            evidence=evidence,
            reasoning=reasoning,
            originality=originality,
            readability=readability_score,
            authority=authority,
            practical_value=practical,
            discussion_potential=discussion,
            overall=overall,
            minimum_publish_score=self.minimum_publish_score,
            publish_ready=overall >= self.minimum_publish_score,
            dimensions=dims,
        )
