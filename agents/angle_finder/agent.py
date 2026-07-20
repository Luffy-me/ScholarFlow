"""Content Angle Finder Agent.

Generates multiple unique LinkedIn angles before writing.
"""

from __future__ import annotations

import json
import re
from typing import Any

from pydantic import BaseModel, Field

from agents.base import Agent, AgentInput, AgentOutput
from agents.memory_builder import approved_experience_texts
from models.base import ChatMessage
from shared.knowledge import load_content_modes, load_user_memory


class Angle(BaseModel):
    type: str
    hook: str
    reason: str
    target_audience: str


class AngleFinderInput(AgentInput):
    pass


class AngleFinderOutput(AgentOutput):
    angles: list[Angle] = Field(default_factory=list)


_ANGLE_TYPES_BY_MODE = {
    "founder": ["contrarian_lesson", "build_in_public", "tradeoff", "mistake_recovery"],
    "researcher": ["evidence_tension", "open_question", "method_critique", "finding_summary"],
    "engineer": ["systems_failure", "implementation_lesson", "quality_gate", "debugging_story"],
    "career_journey": ["transition", "skill_shift", "milestone", "reflection"],
}


def _deterministic_angles(topic: str, audience: str, content_mode: str, memory: dict[str, Any]) -> list[Angle]:
    mode = content_mode if content_mode in _ANGLE_TYPES_BY_MODE else "founder"
    types = _ANGLE_TYPES_BY_MODE[mode]
    approved = approved_experience_texts(memory)
    experience_hint = approved[0] if approved else "recent analysis"
    target = audience or {
        "founder": "founders and operators",
        "researcher": "researchers and analysts",
        "engineer": "engineers and builders",
        "career_journey": "professionals navigating change",
    }.get(mode, "professionals")

    templates = [
        Angle(
            type=types[0],
            hook=f"Most advice on {topic} optimizes for noise. Here's the constraint I actually care about.",
            reason="Contrarian framing creates curiosity without inventing biography.",
            target_audience=target,
        ),
        Angle(
            type=types[1],
            hook=f"While working on {experience_hint}, one pattern around {topic} kept repeating.",
            reason="Grounds the post in an approved experience when available.",
            target_audience=target,
        ),
        Angle(
            type=types[2],
            hook=f"The useful question on {topic} isn't 'what's trending' — it's which tradeoff you're accepting.",
            reason="Tradeoff angles produce opinionated, discussion-friendly posts.",
            target_audience=target,
        ),
        Angle(
            type=types[3 % len(types)],
            hook=f"If I had to explain {topic} in one operational lesson, it would be this.",
            reason="Forces specificity and a clear takeaway.",
            target_audience=target,
        ),
    ]
    return templates


def _parse_angles(raw: str, fallback: list[Angle]) -> list[Angle]:
    text = raw.strip()
    text = re.sub(r"^```(?:json)?\s*", "", text)
    text = re.sub(r"\s*```$", "", text)
    try:
        payload = json.loads(text)
    except json.JSONDecodeError:
        return fallback
    items = payload.get("angles") if isinstance(payload, dict) else payload
    if not isinstance(items, list):
        return fallback
    angles: list[Angle] = []
    for item in items:
        if not isinstance(item, dict):
            continue
        try:
            angles.append(
                Angle(
                    type=str(item.get("type", "general")),
                    hook=str(item.get("hook", "")).strip(),
                    reason=str(item.get("reason", "")).strip(),
                    target_audience=str(item.get("target_audience", "")).strip(),
                )
            )
        except Exception:  # noqa: BLE001
            continue
    angles = [a for a in angles if a.hook]
    return angles if len(angles) >= 2 else fallback


class AngleFinderAgent(Agent[AngleFinderInput, AngleFinderOutput]):
    name = "angle_finder"

    async def run(self, payload: AngleFinderInput) -> AngleFinderOutput:
        memory = payload.user_memory or load_user_memory()
        audience = str((payload.extra or {}).get("audience") or "").strip()
        modes = load_content_modes()
        mode_key = (
            payload.content_mode
            if payload.content_mode in modes.get("modes", {})
            else modes.get("default_mode", "founder")
        )
        fallback = _deterministic_angles(payload.topic, audience, mode_key, memory)
        approved = approved_experience_texts(memory)

        system = (
            "You generate unique LinkedIn content angles.\n"
            "Return JSON only: {\"angles\":[{\"type\":\"\",\"hook\":\"\",\"reason\":\"\",\"target_audience\":\"\"}]}\n"
            "Generate 3-5 distinct angles.\n"
            "Do NOT invent personal experiences, metrics, clients, or quotes.\n"
            f"Approved experiences only (optional to reference): {approved}\n"
            f"Content mode: {mode_key}"
        )
        user = (
            f"Topic: {payload.topic}\n"
            f"Audience: {audience or 'professionals'}\n"
            f"Content mode: {mode_key}\n"
            "Generate angles now."
        )
        result = await self.provider.generate(
            [ChatMessage(role="system", content=system), ChatMessage(role="user", content=user)],
            temperature=0.6,
            response_format="json",
        )
        angles = _parse_angles(result.text, fallback)
        return AngleFinderOutput(
            text=json.dumps({"angles": [a.model_dump() for a in angles]}),
            angles=angles,
            data={"angles": [a.model_dump() for a in angles], "selected_mode": mode_key},
            meta={"provider": result.provider, "model": result.model},
        )
