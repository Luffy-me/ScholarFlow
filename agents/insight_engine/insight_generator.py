"""Insight Engine — original insights before content creation."""

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
    r"opposite|myth|wrong|less|fewer|bottleneck)\b",
    re.I,
)


def _blob(insight: Insight) -> str:
    return " ".join(
        [
            insight.core_insight,
            insight.why_it_matters,
            insight.common_belief,
            insight.new_perspective,
            insight.supporting_evidence,
            insight.reader_takeaway,
        ]
    ).strip()


def evaluate_insight_quality(insight: Insight, *, topic: str = "") -> InsightQuality:
    """Score insight strength without claiming authorship or virality."""
    flags: list[str] = []
    text = _blob(insight).lower()
    score = 40

    if not insight.core_insight.strip():
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

    # Obvious conclusion: belief and perspective nearly identical
    belief = insight.common_belief.strip().lower()
    perspective = insight.new_perspective.strip().lower()
    has_contrast = bool(belief and perspective and belief != perspective)
    if has_contrast:
        # Soft overlap check
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

    if _COUNTERINTUITIVE_RE.search(insight.core_insight) or _COUNTERINTUITIVE_RE.search(
        insight.new_perspective
    ):
        score += 12
    else:
        flags.append("lacks_counterintuitive_edge")

    # Specificity signals: tools, experiments, named systems
    if re.search(
        r"\b(RAG|Qwen|Ollama|evaluation loop|MacBook|ScholarFlow|benchmark|experiment|"
        r"workflow|prompt|retrieval|chunking)\b",
        _blob(insight),
        re.I,
    ):
        score += 14
    elif topic and topic.lower() in {"ai", "artificial intelligence", "the future of ai"}:
        # Broad AI topics without specifics stay weak.
        score -= 8
        flags.append("broad_topic_without_specificity")

    if insight.supporting_evidence.strip():
        score += 6
    else:
        flags.append("thin_evidence")

    strength = clamp_score(score)
    is_strong = strength >= 65 and has_contrast and takeaway_actionable and "generic_observation" not in flags
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
    insight = Insight(
        core_insight=str(payload.get("core_insight", "")).strip(),
        why_it_matters=str(payload.get("why_it_matters", "")).strip(),
        common_belief=str(payload.get("common_belief", "")).strip(),
        new_perspective=str(payload.get("new_perspective", "")).strip(),
        supporting_evidence=str(payload.get("supporting_evidence", "")).strip(),
        reader_takeaway=str(payload.get("reader_takeaway", "")).strip(),
    )
    if not insight.core_insight:
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
    """Fallback insight that stays specific when memory exists, weak when topic is generic."""
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
        # Intentionally weak: mirrors generic AI commentary so quality scoring can reject it.
        return Insight(
            core_insight="AI is changing everything across industries.",
            why_it_matters="The future of work depends on embracing digital transformation.",
            common_belief="AI will transform every industry.",
            new_perspective="AI is transforming every industry, so teams should stay ahead of the curve.",
            supporting_evidence="",
            reader_takeaway="Believe in yourself and unlock your potential with AI.",
        )

    if experience:
        core = (
            f"After {experience[0].lower() + experience[1:] if experience else 'recent work'}, "
            f"the useful lesson on {topic} is that process design beats slogans."
        )
        # Cleaner core when experience is already a sentence-like statement.
        if experience.lower().startswith(("built", "compared", "tested", "i ")):
            core = (
                f"A lesson from '{experience}' on {topic}: the bottleneck is usually the evaluation "
                f"loop, not the headline tool."
            )
        evidence = experience
        takeaway = (
            f"Pick one workflow step in your {topic} process, write a failing test for quality, "
            f"and measure whether a bigger model still helps."
        )
        common = f"Most people assume better {topic} outcomes come from bigger/better models or tools."
        perspective = (
            f"In practice, constrained experiments and clearer evaluation criteria create more lift "
            f"than switching tools."
        )
    else:
        finding = findings[0] if findings else f"specific operating constraints around {topic}"
        core = (
            f"For {topic}, progress usually stalls on an unstated tradeoff — not on missing inspiration."
        )
        evidence = finding if findings else trend_why or f"Research framing on {topic}"
        takeaway = (
            f"Write down the constraint you are optimizing for in {topic}, then cut one step that "
            f"does not serve it."
        )
        common = f"Common belief: more information or more tooling automatically improves {topic}."
        perspective = (
            f"New perspective: clarifying the constraint and testing one change beats collecting "
            f"generic best practices."
        )

    return Insight(
        core_insight=core,
        why_it_matters=(
            trend_why
            or f"Operators working on {topic} waste cycles on generic advice that ignores their real bottleneck."
        ),
        common_belief=common,
        new_perspective=perspective,
        supporting_evidence=evidence,
        reader_takeaway=takeaway,
    )


class InsightGenerator:
    """Generate and quality-score an original insight."""

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
        meta: dict[str, Any] = {"deterministic": True}

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
                temperature=0.4,
                response_format="json",
            )
            parsed = _parse_insight(result.text)
            meta = {"provider": result.provider, "model": result.model, "deterministic": False}
            if parsed is not None:
                insight = parsed
                # If the model returns a weak generic insight while we have strong memory,
                # prefer the deterministic specific fallback.
                llm_quality = evaluate_insight_quality(insight, topic=payload.topic)
                fallback_quality = evaluate_insight_quality(fallback, topic=payload.topic)
                if llm_quality.is_weak and fallback_quality.strength_score > llm_quality.strength_score:
                    insight = fallback
                    meta["replaced_weak_llm"] = True
            else:
                insight = fallback
                meta["deterministic"] = True
                meta["parse_fallback"] = True

        quality = evaluate_insight_quality(insight, topic=payload.topic)
        return InsightEngineOutput(
            text=insight.core_insight,
            insight=insight,
            quality=quality,
            data=insight.as_dict(),
            meta=meta,
        )


# Pipeline-friendly alias
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
    # Preserve explicit empty list so callers can force "no memory" weak-insight paths.
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
