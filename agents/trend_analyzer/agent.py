"""Trend Analysis Agent — lightweight framing before Insight Engine.

Not a full scraper yet. Produces structured trend context from topic + research.
"""

from __future__ import annotations

import json
import re
from typing import Any

from agents.base import Agent, AgentInput, AgentOutput
from models.base import ChatMessage


class TrendAnalyzerInput(AgentInput):
    pass


class TrendAnalyzerOutput(AgentOutput):
    pass


class TrendAnalyzerAgent(Agent[TrendAnalyzerInput, TrendAnalyzerOutput]):
    name = "trend_analyzer"

    async def run(self, payload: TrendAnalyzerInput) -> TrendAnalyzerOutput:
        extra = payload.extra or {}
        audience = str(extra.get("audience") or "").strip()
        research = extra.get("research") if isinstance(extra.get("research"), dict) else {}

        system = (
            "You are a LinkedIn trend analyst.\n"
            "Return JSON with topic, trend_level (emerging|rising|saturated|unclear), "
            "why_it_matters, possible_angles (array of strings), target_audience, "
            "saturation_risk, opportunity.\n"
            "Do not invent statistics, sources, or personal experiences.\n"
            "Be specific about what is becoming crowded vs still useful."
        )
        user = (
            f"Topic: {payload.topic}\n"
            f"Audience: {audience or 'professionals'}\n"
            f"Content mode: {payload.content_mode}\n"
            f"Research briefing: {json.dumps(research)}\n"
            "Produce trend analysis JSON."
        )
        result = await self.provider.generate(
            [ChatMessage(role="system", content=system), ChatMessage(role="user", content=user)],
            temperature=0.3,
            response_format="json",
        )
        data = _parse_or_fallback(result.text, payload.topic, audience, research)
        return TrendAnalyzerOutput(
            text=json.dumps(data),
            data=data,
            meta={"provider": result.provider, "model": result.model},
        )


def _parse_or_fallback(
    raw: str,
    topic: str,
    audience: str,
    research: dict[str, Any],
) -> dict[str, Any]:
    text = raw.strip()
    text = re.sub(r"^```(?:json)?\s*", "", text)
    text = re.sub(r"\s*```$", "", text)
    try:
        payload = json.loads(text)
        if isinstance(payload, dict) and (
            payload.get("topic") is not None or payload.get("trend_level")
        ):
            angles = payload.get("possible_angles") or []
            if not isinstance(angles, list):
                angles = []
            return {
                "topic": payload.get("topic") or topic,
                "trend_level": str(payload.get("trend_level") or "unclear"),
                "why_it_matters": str(payload.get("why_it_matters") or "").strip(),
                "possible_angles": [str(a) for a in angles if str(a).strip()],
                "target_audience": str(payload.get("target_audience") or audience or "professionals"),
                "saturation_risk": str(payload.get("saturation_risk") or "").strip(),
                "opportunity": str(payload.get("opportunity") or "").strip(),
                "status": "ok",
            }
    except json.JSONDecodeError:
        pass

    findings = [str(x) for x in (research.get("key_findings") or []) if str(x).strip()]
    broad = (topic or "").strip().lower() in {"ai", "artificial intelligence", "the future of ai"}
    return {
        "topic": topic,
        "trend_level": "saturated" if broad else "rising",
        "why_it_matters": (
            "Broad AI commentary is crowded; specific operating lessons still travel."
            if broad
            else (
                findings[0]
                if findings
                else f"Practitioners need concrete tradeoffs on {topic}, not slogans."
            )
        ),
        "possible_angles": [
            "constraint-first lesson",
            "experiment vs hype",
            "implementation tradeoff",
        ],
        "target_audience": audience or "professionals",
        "saturation_risk": "high" if broad else "medium",
        "opportunity": (
            "Replace generic AI takes with a verified experiment lesson."
            if broad
            else f"Surface one counterintuitive operating lesson on {topic}."
        ),
        "status": "fallback",
    }
