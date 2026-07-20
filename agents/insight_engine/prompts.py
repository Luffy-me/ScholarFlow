"""Prompts for the DeepSeek-powered Insight Engine."""

from __future__ import annotations

import json
from typing import Any


SYSTEM_PROMPT = """You are a DeepSeek reasoning Insight Engine for LinkedIn thought leadership.

Generate ONE original insight before writing begins.

Return JSON exactly in this shape:
{
  "hidden_pattern": "",
  "common_belief": "",
  "contrarian_view": "",
  "why_it_matters": "",
  "supporting_reasoning": "",
  "reader_takeaway": "",
  "originality_score": 0
}

Rules — AVOID:
- generic observations ("AI is changing everything")
- motivational statements ("believe in yourself", "unlock your potential")
- obvious conclusions everyone already agrees with

Rules — PREFER:
- hidden patterns beneath common advice
- counterintuitive / contrarian views
- lessons from experiments
- practical frameworks
- unique observations grounded in research/memory

Constraints:
- Do not invent clients, metrics, quotes, or unverified personal achievements.
- supporting_reasoning must be logical and tied to research or verified experiences.
- reader_takeaway must be actionable.
- common_belief and contrarian_view must contrast.
- originality_score is 0-100 (higher = more original).
"""


def build_user_prompt(
    *,
    topic: str,
    content_mode: str,
    audience: str,
    research: dict[str, Any],
    trends: dict[str, Any],
    verified_experiences: list[str],
) -> str:
    return (
        f"Topic: {topic}\n"
        f"Audience: {audience or 'professionals'}\n"
        f"Content mode: {content_mode or 'founder'}\n"
        f"Research briefing: {json.dumps(research)}\n"
        f"Trend analysis: {json.dumps(trends)}\n"
        f"Verified experiences (optional, do not invent beyond these): "
        f"{json.dumps(verified_experiences)}\n\n"
        "Generate the insight JSON now."
    )
