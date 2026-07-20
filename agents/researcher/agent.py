"""Research Agent — lightweight topic framing (no invented personal facts)."""

from __future__ import annotations

import json
from typing import Any

from agents.base import Agent, AgentInput, AgentOutput
from models.base import ChatMessage


class ResearcherInput(AgentInput):
    pass


class ResearcherOutput(AgentOutput):
    pass


class ResearcherAgent(Agent[ResearcherInput, ResearcherOutput]):
    name = "researcher"

    async def run(self, payload: ResearcherInput) -> ResearcherOutput:
        audience = str((payload.extra or {}).get("audience") or "").strip()
        system = (
            "You are a research briefing assistant for LinkedIn thought leadership.\n"
            "Return JSON with topic, key_findings (array of strings), sources (array), open_questions (array).\n"
            "Do not invent personal experiences, clients, or metrics.\n"
            "If you lack sources, leave sources empty and keep findings cautious."
        )
        user = (
            f"Topic: {payload.topic}\n"
            f"Audience: {audience or 'professionals'}\n"
            f"Content mode: {payload.content_mode}\n"
            "Produce a brief research framing."
        )
        result = await self.provider.generate(
            [ChatMessage(role="system", content=system), ChatMessage(role="user", content=user)],
            temperature=0.3,
            response_format="json",
        )
        data = _safe_json(result.text, payload.topic)
        return ResearcherOutput(
            text=json.dumps(data),
            data=data,
            meta={"provider": result.provider, "model": result.model},
        )


def _safe_json(raw: str, topic: str) -> dict[str, Any]:
    try:
        payload = json.loads(raw)
        if isinstance(payload, dict):
            return {
                "topic": payload.get("topic") or topic,
                "key_findings": payload.get("key_findings") or [],
                "sources": payload.get("sources") or [],
                "open_questions": payload.get("open_questions") or [],
                "status": "ok",
            }
    except json.JSONDecodeError:
        pass
    return {
        "topic": topic,
        "key_findings": [
            f"Clarify the operational tradeoff behind {topic}.",
            "Prefer specific systems over slogans.",
        ],
        "sources": [],
        "open_questions": [f"What constraint actually limits progress on {topic}?"],
        "status": "fallback",
    }
