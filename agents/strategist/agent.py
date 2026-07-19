"""Content Strategist Agent — choose direction from research + selected angle."""

from __future__ import annotations

import json
from typing import Any

from agents.base import Agent, AgentInput, AgentOutput
from models.base import ChatMessage


class StrategistInput(AgentInput):
    pass


class StrategistOutput(AgentOutput):
    pass


class StrategistAgent(Agent[StrategistInput, StrategistOutput]):
    name = "strategist"

    async def run(self, payload: StrategistInput) -> StrategistOutput:
        extra = payload.extra or {}
        audience = str(extra.get("audience") or "").strip()
        angle = extra.get("angle") or {}
        research = extra.get("research") or {}

        system = (
            "You are a LinkedIn content strategist.\n"
            "Return JSON with audience, hook, opinion, structure, discussion_question.\n"
            "Use the provided angle when available.\n"
            "Do not invent personal experiences, metrics, clients, or quotes."
        )
        user = (
            f"Topic: {payload.topic}\n"
            f"Audience: {audience}\n"
            f"Content mode: {payload.content_mode}\n"
            f"Selected angle: {json.dumps(angle)}\n"
            f"Research: {json.dumps(research)}\n"
            "Produce strategy now."
        )
        result = await self.provider.generate(
            [ChatMessage(role="system", content=system), ChatMessage(role="user", content=user)],
            temperature=0.4,
            response_format="json",
        )
        data = _safe_strategy(result.text, payload.topic, audience, angle)
        return StrategistOutput(
            text=json.dumps(data),
            data=data,
            meta={"provider": result.provider, "model": result.model},
        )


def _safe_strategy(raw: str, topic: str, audience: str, angle: dict[str, Any]) -> dict[str, Any]:
    try:
        payload = json.loads(raw)
        if isinstance(payload, dict) and payload.get("hook"):
            return {
                "audience": payload.get("audience") or audience or "professionals",
                "hook": payload.get("hook"),
                "opinion": payload.get("opinion") or "",
                "structure": payload.get("structure") or "",
                "discussion_question": payload.get("discussion_question") or "",
                "status": "ok",
            }
    except json.JSONDecodeError:
        pass
    hook = str(angle.get("hook") or f"One practical lens on {topic}:")
    return {
        "audience": audience or str(angle.get("target_audience") or "professionals"),
        "hook": hook,
        "opinion": "Specific systems beat generic advice.",
        "structure": "hook → concrete observation → lesson → question",
        "discussion_question": f"What constraint is shaping your approach to {topic}?",
        "status": "fallback",
    }
