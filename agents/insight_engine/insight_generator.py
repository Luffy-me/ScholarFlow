"""Insight Engine — DeepSeek reasoning for original insights before writing."""

from __future__ import annotations

import json
import re
from typing import Any

from agents.insight_engine.prompts import SYSTEM_PROMPT, build_user_prompt
from agents.insight_engine.schemas import (
    Insight,
    InsightEngineInput,
    InsightEngineOutput,
    InsightQuality,
)
from agents.memory_builder import approved_experience_texts
from models.base import ChatMessage, ModelProvider
from shared.knowledge import load_user_memory
from shared.quality import clamp_score


_GENERIC_PHRASES = [
    "ai is changing everything",
    "ai is transforming",
    "in today's world",
    "the future of",
    "digital transformation",
    "game changer",
    "unlock your potential",
    "believe in yourself",
    "success is a journey",
    "think outside the box",
    "embrace change",
    "stay ahead of the curve",
    "leverage ai",
    "revolutionizing",
    "at the end of the day",
]

_MOTIVATIONAL_RE = re.compile(
    r"\b(believe in yourself|unlock your potential|you've got this|hustle|"
    r"never give up|dream big|manifest|inspire yourself)\b",
    re.I,
)

_ACTIONABLE_RE = re.compile(
    r"\b(try|test|measure|write|build|cut|replace|ask|track|run|compare|"
    r"remove|define|ship|instrument|log|review|audit|benchmark)\b",
    re.I,
)

_COUNTERINTUITIVE_RE = re.compile(
    r"\b(not|instead|rather than|tradeoff|constraint|surprising|counter|"
    r"opposite|myth|wrong|less|fewer|bottleneck|hidden)\b",
    re.I,
)


def _blob(insight: Insight) -> str:
    return " ".join(
        [
            insight.hidden_pattern,
            insight.why_it_matters,
            insight.common_belief,
            insight.contrarian_view,
            insight.supporting_reasoning,
            insight.reader_takeaway,
        ]
    ).strip()


def evaluate_insight_quality(insight: Insight, *, topic: str = "") -> InsightQuality:
    """Score insight strength without claiming authorship or virality."""
    flags: list[str] = []
    text = _blob(insight).lower()
    score = 40

    if not insight.hidden_pattern.strip():
        flags.append("missing_core_insight")
        return InsightQuality(
            strength_score=0,
            is_weak=True,
            is_strong=False,
            has_belief_contrast=False,
            takeaway_actionable=False,
            flags=flags,
        )

    generic_hits = [p for p in _GENERIC_PHRASES if p in text]
    if generic_hits:
        score -= 18 * min(3, len(generic_hits))
        flags.append("generic_observation")

    if _MOTIVATIONAL_RE.search(text):
        score -= 25
        flags.append("motivational_statement")

    belief = insight.common_belief.strip().lower()
    perspective = insight.contrarian_view.strip().lower()
    has_contrast = bool(belief and perspective and belief != perspective)
    if has_contrast:
        belief_tokens = set(re.findall(r"[a-z]{4,}", belief))
        perspective_tokens = set(re.findall(r"[a-z]{4,}", perspective))
        if belief_tokens and perspective_tokens:
            overlap = len(belief_tokens & perspective_tokens) / max(
                1, len(belief_tokens | perspective_tokens)
            )
            if overlap > 0.7:
                has_contrast = False
                flags.append("obvious_conclusion")
                score -= 15
            else:
                score += 18
        else:
            score += 12
    else:
        flags.append("missing_belief_contrast")
        score -= 12

    takeaway = insight.reader_takeaway.strip()
    takeaway_actionable = bool(takeaway) and bool(_ACTIONABLE_RE.search(takeaway))
    if takeaway_actionable:
        score += 16
    else:
        flags.append("takeaway_not_actionable")
        score -= 10

    if _COUNTERINTUITIVE_RE.search(insight.hidden_pattern) or _COUNTERINTUITIVE_RE.search(
        insight.contrarian_view
    ):
        score += 12
    else:
        flags.append("lacks_counterintuitive_edge")

    if re.search(
        r"\b(RAG|Qwen|Ollama|evaluation loop|MacBook|ScholarFlow|benchmark|experiment|"
        r"workflow|prompt|retrieval|chunking|DeepSeek)\b",
        _blob(insight),
        re.I,
    ):
        score += 14
    elif topic and topic.lower() in {"ai", "artificial intelligence", "the future of ai"}:
        score -= 8
        flags.append("broad_topic_without_specificity")

    if insight.supporting_reasoning.strip():
        score += 6
    else:
        flags.append("thin_evidence")

    # Blend model-provided originality when present.
    if insight.originality_score:
        score = int(round((score * 0.7) + (insight.originality_score * 0.3)))

    strength = clamp_score(score)
    is_strong = (
        strength >= 65
        and has_contrast
        and takeaway_actionable
        and "generic_observation" not in flags
    )
    is_weak = strength < 55 or "generic_observation" in flags or "motivational_statement" in flags

    return InsightQuality(
        strength_score=strength,
        is_weak=is_weak,
        is_strong=is_strong,
        has_belief_contrast=has_contrast,
        takeaway_actionable=takeaway_actionable,
        flags=flags,
    )


def _parse_insight(raw: str) -> Insight | None:
    text = raw.strip()
    text = re.sub(r"^```(?:json)?\s*", "", text)
    text = re.sub(r"\s*```$", "", text)
    try:
        payload = json.loads(text)
    except json.JSONDecodeError:
        return None
    if not isinstance(payload, dict):
        return None

    hidden = str(
        payload.get("hidden_pattern")
        or payload.get("core_insight")
        or ""
    ).strip()
    contrarian = str(
        payload.get("contrarian_view")
        or payload.get("new_perspective")
        or ""
    ).strip()
    reasoning = str(
        payload.get("supporting_reasoning")
        or payload.get("supporting_evidence")
        or ""
    ).strip()

    insight = Insight(
        hidden_pattern=hidden,
        why_it_matters=str(payload.get("why_it_matters", "")).strip(),
        common_belief=str(payload.get("common_belief", "")).strip(),
        contrarian_view=contrarian,
        supporting_reasoning=reasoning,
        reader_takeaway=str(payload.get("reader_takeaway", "")).strip(),
        originality_score=clamp_score(payload.get("originality_score", 0) or 0),
    )
    if not insight.hidden_pattern:
        return None
    return insight


def _deterministic_insight(
    *,
    topic: str,
    content_mode: str,
    audience: str,
    research: dict[str, Any],
    trends: dict[str, Any],
    verified: list[str],
) -> Insight:
    topic_l = (topic or "").strip().lower()
    findings = [str(x) for x in (research.get("key_findings") or []) if str(x).strip()]
    trend_why = str((trends or {}).get("why_it_matters") or "").strip()
    experience = verified[0] if verified else ""

    broad_ai = topic_l in {
        "ai",
        "artificial intelligence",
        "the future of ai",
        "ai trends",
        "generative ai",
    } and not experience and not findings

    if broad_ai:
        return Insight(
            hidden_pattern="AI is changing everything across industries.",
            why_it_matters="The future of work depends on embracing digital transformation.",
            common_belief="AI will transform every industry.",
            contrarian_view="AI is transforming every industry, so teams should stay ahead of the curve.",
            supporting_reasoning="",
            reader_takeaway="Believe in yourself and unlock your potential with AI.",
            originality_score=15,
        )

    if experience:
        if experience.lower().startswith(("built", "compared", "tested", "i ")):
            hidden = (
                f"A hidden pattern from '{experience}' on {topic}: the bottleneck is usually "
                f"the evaluation loop, not the headline tool."
            )
        else:
            hidden = (
                f"After {experience}, the hidden pattern on {topic} is that process design "
                f"beats slogans."
            )
        return Insight(
            hidden_pattern=hidden,
            why_it_matters=(
                trend_why
                or f"Operators working on {topic} waste cycles on generic advice that ignores their real bottleneck."
            ),
            common_belief=f"Most people assume better {topic} outcomes come from bigger/better models or tools.",
            contrarian_view=(
                "In practice, constrained experiments and clearer evaluation criteria create more lift "
                "than switching tools."
            ),
            supporting_reasoning=experience,
            reader_takeaway=(
                f"Pick one workflow step in your {topic} process, write a failing test for quality, "
                f"and measure whether a bigger model still helps."
            ),
            originality_score=78,
        )

    finding = findings[0] if findings else f"specific operating constraints around {topic}"
    return Insight(
        hidden_pattern=(
            f"For {topic}, progress usually stalls on an unstated tradeoff — not on missing inspiration."
        ),
        why_it_matters=(
            trend_why
            or f"Operators working on {topic} waste cycles on generic advice that ignores their real bottleneck."
        ),
        common_belief=f"Common belief: more information or more tooling automatically improves {topic}.",
        contrarian_view=(
            "Contrarian view: clarifying the constraint and testing one change beats collecting "
            "generic best practices."
        ),
        supporting_reasoning=finding if findings else trend_why or f"Research framing on {topic}",
        reader_takeaway=(
            f"Write down the constraint you are optimizing for in {topic}, then cut one step that "
            f"does not serve it."
        ),
        originality_score=66,
    )


class InsightGenerator:
    """Generate and quality-score an original insight via DeepSeek reasoning."""

    name = "insight_engine"

    def __init__(self, provider: ModelProvider | None = None) -> None:
        self.provider = provider

    async def run(self, payload: InsightEngineInput) -> InsightEngineOutput:
        memory = payload.user_memory or load_user_memory()
        extra = payload.extra or {}
        audience = str(extra.get("audience") or "").strip()
        research = extra.get("research") if isinstance(extra.get("research"), dict) else {}
        trends = extra.get("trends") if isinstance(extra.get("trends"), dict) else {}
        if "verified_experiences" in extra:
            verified = [str(x) for x in (extra.get("verified_experiences") or []) if str(x).strip()]
        else:
            verified = approved_experience_texts(memory)

        fallback = _deterministic_insight(
            topic=payload.topic,
            content_mode=payload.content_mode or "founder",
            audience=audience,
            research=research or {},
            trends=trends or {},
            verified=verified,
        )

        insight = fallback
        meta: dict[str, Any] = {"deterministic": True, "reasoning_family": "deepseek"}

        if self.provider is not None:
            user = build_user_prompt(
                topic=payload.topic,
                content_mode=payload.content_mode or "founder",
                audience=audience,
                research=research or {},
                trends=trends or {},
                verified_experiences=verified,
            )
            result = await self.provider.generate(
                [
                    ChatMessage(role="system", content=SYSTEM_PROMPT),
                    ChatMessage(role="user", content=user),
                ],
                temperature=0.3,
                response_format="json",
            )
            parsed = _parse_insight(result.text)
            meta = {
                "provider": result.provider,
                "model": result.model,
                "deterministic": False,
                "reasoning_family": "deepseek",
            }
            if parsed is not None:
                insight = parsed
                if not insight.originality_score:
                    insight.originality_score = evaluate_insight_quality(
                        insight, topic=payload.topic
                    ).strength_score
                llm_quality = evaluate_insight_quality(insight, topic=payload.topic)
                fallback_quality = evaluate_insight_quality(fallback, topic=payload.topic)
                if llm_quality.is_weak and fallback_quality.strength_score > llm_quality.strength_score:
                    insight = fallback
                    meta["replaced_weak_llm"] = True
            else:
                insight = fallback
                meta["deterministic"] = True
                meta["parse_fallback"] = True

        if not insight.originality_score:
            insight.originality_score = evaluate_insight_quality(
                insight, topic=payload.topic
            ).strength_score

        quality = evaluate_insight_quality(insight, topic=payload.topic)
        return InsightEngineOutput(
            text=insight.hidden_pattern,
            insight=insight,
            quality=quality,
            data=insight.as_dict(),
            meta=meta,
        )


InsightEngineAgent = InsightGenerator


async def generate_insight(
    provider: ModelProvider | None,
    *,
    topic: str,
    content_mode: str = "founder",
    audience: str = "",
    research: dict[str, Any] | None = None,
    trends: dict[str, Any] | None = None,
    user_memory: dict[str, Any] | None = None,
    verified_experiences: list[str] | None = None,
) -> InsightEngineOutput:
    agent = InsightGenerator(provider)
    extra: dict[str, Any] = {
        "audience": audience,
        "research": research or {},
        "trends": trends or {},
    }
    if verified_experiences is not None:
        extra["verified_experiences"] = list(verified_experiences)
    return await agent.run(
        InsightEngineInput(
            topic=topic,
            content_mode=content_mode,
            user_memory=user_memory if user_memory is not None else {},
            extra=extra,
        )
    )
