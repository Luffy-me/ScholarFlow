"""Debate Mode — Qwen writes, DeepSeek critiques, Qwen rewrites, DeepSeek scores."""

from __future__ import annotations

import json
import re
from typing import Any

from agents.debate.schemas import DebateFinalScore, DebateResult, DebateReview
from agents.humanizer import HumanizerAgent, HumanizerInput
from agents.writer import WriterAgent, WriterInput
from models.base import ChatMessage, ModelProvider
from shared.quality import clamp_score, scan_text


_REVIEW_SYSTEM = """You are a DeepSeek debate critic for LinkedIn drafts.

Review the draft for:
- generic ideas
- weak arguments
- missing evidence
- lack of originality
- AI writing patterns (pattern risk only — never claim authorship)

Return JSON:
{
  "generic_ideas": [],
  "weak_arguments": [],
  "missing_evidence": [],
  "originality_issues": [],
  "ai_writing_patterns": [],
  "improvements": [],
  "rejected": false,
  "reject_reason": "",
  "review_score": 0
}

Set rejected=true when the draft is dominated by generic/motivational AI writing
with no specific insight or evidence.
"""

_FINAL_SYSTEM = """You are a DeepSeek final scorer after a rewrite debate.

Return JSON:
{
  "final_score": 0,
  "originality_score": 0,
  "argument_strength": 0,
  "evidence_score": 0,
  "ai_pattern_risk": 0,
  "accepted": false,
  "summary": ""
}

accepted=true only if the rewrite is specific, original enough, and not generic AI filler.
Never claim the text was written by AI or by a human.
"""


def _parse_json(raw: str) -> dict[str, Any]:
    text = raw.strip()
    text = re.sub(r"^```(?:json)?\s*", "", text)
    text = re.sub(r"\s*```$", "", text)
    try:
        payload = json.loads(text)
        return payload if isinstance(payload, dict) else {}
    except json.JSONDecodeError:
        return {}


def _deterministic_review(text: str, memory: dict[str, Any] | None) -> DebateReview:
    scan = scan_text(text, memory)
    generic = [h.matched for h in scan.banned_phrases]
    weak = [h.matched for h in scan.weak_hooks]
    patterns = generic + [h.matched for h in scan.fake_experiences]
    rejected = bool(scan.has_generic_ai and not scan.has_strong_first_person)
    score = 25 if rejected else (55 if scan.has_generic_ai else 72)
    improvements: list[str] = []
    if scan.has_generic_ai:
        improvements.append("Replace generic openings with a specific observation.")
    if scan.has_weak_hook:
        improvements.append("Rewrite the hook to a concrete tension or tradeoff.")
    if scan.has_fake_experience:
        improvements.append("Remove ungrounded personal claims.")
    if not improvements:
        improvements.append("Tighten the argument and add one verified detail.")
    return DebateReview(
        generic_ideas=generic,
        weak_arguments=weak,
        missing_evidence=["Add verified evidence"] if rejected or scan.has_fake_experience else [],
        originality_issues=["Sounds template-like"] if scan.has_generic_ai else [],
        ai_writing_patterns=patterns,
        improvements=improvements,
        rejected=rejected,
        reject_reason="Generic AI writing patterns dominate the draft." if rejected else "",
        review_score=score,
    )


def _deterministic_final(text: str, memory: dict[str, Any] | None, review: DebateReview) -> DebateFinalScore:
    scan = scan_text(text, memory)
    risk = 85 if scan.has_generic_ai else 20
    originality = 25 if scan.has_generic_ai else 75
    evidence = 20 if scan.has_fake_experience else 70
    argument = 30 if review.rejected else 72
    final = clamp_score((originality + evidence + argument + (100 - risk)) / 4)
    accepted = final >= 60 and not scan.has_generic_ai
    return DebateFinalScore(
        final_score=final,
        originality_score=originality,
        argument_strength=argument,
        evidence_score=evidence,
        ai_pattern_risk=risk,
        accepted=accepted,
        summary=(
            "Rejected: still dominated by generic AI writing patterns."
            if not accepted
            else "Accepted after debate rewrite: specific enough to publish for review."
        ),
    )


class DebateMode:
    """High-quality post loop: Qwen → DeepSeek review → Qwen rewrite → DeepSeek score."""

    def __init__(
        self,
        *,
        writer_provider: ModelProvider,
        critic_provider: ModelProvider,
        rewrite_provider: ModelProvider | None = None,
    ) -> None:
        self.writer_provider = writer_provider
        self.critic_provider = critic_provider
        self.rewrite_provider = rewrite_provider or writer_provider

    async def run(
        self,
        *,
        topic: str,
        content_mode: str,
        format: str,
        user_memory: dict[str, Any],
        writer_extra: dict[str, Any] | None = None,
        initial_draft: str | None = None,
    ) -> DebateResult:
        meta: dict[str, Any] = {"steps": []}

        if initial_draft:
            draft_v1 = initial_draft.strip()
            meta["steps"].append({"step": "write", "source": "provided_draft"})
        else:
            writer = WriterAgent(self.writer_provider)
            written = await writer.run(
                WriterInput(
                    topic=topic,
                    content_mode=content_mode,
                    format=format,
                    user_memory=user_memory,
                    extra=writer_extra or {},
                )
            )
            draft_v1 = written.text
            meta["steps"].append(
                {
                    "step": "write",
                    "provider": written.meta.get("provider"),
                    "model": written.meta.get("model"),
                    "family": "qwen",
                }
            )

        review = await self._review(draft_v1, user_memory)
        meta["steps"].append({"step": "deepseek_review", "rejected": review.rejected})

        # Step 3: Qwen rewrite using DeepSeek improvements (even if rejected, try to salvage).
        humanizer = HumanizerAgent(self.rewrite_provider)
        rewritten = await humanizer.run(
            HumanizerInput(
                text=draft_v1,
                topic=topic,
                user_memory=user_memory,
                extra={"improvements": review.improvements},
            )
        )
        draft_v2 = rewritten.text
        meta["steps"].append(
            {
                "step": "qwen_rewrite",
                "provider": rewritten.meta.get("provider"),
                "model": rewritten.meta.get("model"),
                "family": "qwen",
            }
        )

        final = await self._final_score(draft_v2, user_memory, review)
        meta["steps"].append(
            {
                "step": "deepseek_final",
                "accepted": final.accepted,
                "final_score": final.final_score,
            }
        )

        generic_rejected = review.rejected or (not final.accepted and final.ai_pattern_risk >= 70)

        return DebateResult(
            enabled=True,
            draft_v1=draft_v1,
            review=review,
            draft_v2=draft_v2,
            final_score=final,
            generic_rejected=generic_rejected,
            meta=meta,
        )

    async def _review(self, text: str, memory: dict[str, Any]) -> DebateReview:
        result = await self.critic_provider.generate(
            [
                ChatMessage(role="system", content=_REVIEW_SYSTEM),
                ChatMessage(role="user", content=text or "Empty draft"),
            ],
            temperature=0.1,
            response_format="json",
        )
        payload = _parse_json(result.text)
        if not payload:
            return _deterministic_review(text, memory)

        review = DebateReview(
            generic_ideas=[str(x) for x in payload.get("generic_ideas", [])],
            weak_arguments=[str(x) for x in payload.get("weak_arguments", [])],
            missing_evidence=[str(x) for x in payload.get("missing_evidence", [])],
            originality_issues=[str(x) for x in payload.get("originality_issues", [])],
            ai_writing_patterns=[str(x) for x in payload.get("ai_writing_patterns", [])],
            improvements=[str(x) for x in payload.get("improvements", [])],
            rejected=bool(payload.get("rejected", False)),
            reject_reason=str(payload.get("reject_reason", "")),
            review_score=clamp_score(payload.get("review_score", 50)),
        )
        # Hard gate from deterministic scan — never accept pure generic filler.
        hard = _deterministic_review(text, memory)
        if hard.rejected:
            review.rejected = True
            review.reject_reason = review.reject_reason or hard.reject_reason
            review.generic_ideas = list(dict.fromkeys(review.generic_ideas + hard.generic_ideas))
            review.ai_writing_patterns = list(
                dict.fromkeys(review.ai_writing_patterns + hard.ai_writing_patterns)
            )
            review.improvements = list(dict.fromkeys(review.improvements + hard.improvements))
            review.review_score = min(review.review_score, hard.review_score)
        return review

    async def _final_score(
        self,
        text: str,
        memory: dict[str, Any],
        review: DebateReview,
    ) -> DebateFinalScore:
        result = await self.critic_provider.generate(
            [
                ChatMessage(role="system", content=_FINAL_SYSTEM),
                ChatMessage(
                    role="user",
                    content=json.dumps({"draft": text, "prior_review": review.model_dump()}),
                ),
            ],
            temperature=0.1,
            response_format="json",
        )
        payload = _parse_json(result.text)
        if not payload:
            return _deterministic_final(text, memory, review)

        final = DebateFinalScore(
            final_score=clamp_score(payload.get("final_score", 50)),
            originality_score=clamp_score(payload.get("originality_score", 50)),
            argument_strength=clamp_score(payload.get("argument_strength", 50)),
            evidence_score=clamp_score(payload.get("evidence_score", 50)),
            ai_pattern_risk=clamp_score(payload.get("ai_pattern_risk", 50)),
            accepted=bool(payload.get("accepted", False)),
            summary=str(payload.get("summary", "")),
        )
        hard = _deterministic_final(text, memory, review)
        if hard.ai_pattern_risk >= 70:
            final.accepted = False
            final.ai_pattern_risk = max(final.ai_pattern_risk, hard.ai_pattern_risk)
            final.final_score = min(final.final_score, hard.final_score)
            final.summary = hard.summary
        return final
