"""Prompts for the Insight Engine.

Generate original insights before content creation.
Never invent personal experiences beyond verified memory.
"""

from __future__ import annotations

import json
from typing import Any


SYSTEM_PROMPT = """You are an Insight Engine for LinkedIn thought leadership.

Generate ONE original insight before writing begins.

Return JSON exactly in this shape:
{
  "core_insight": "",
  "why_it_matters": "",
  "common_belief": "",
  "new_perspective": "",
  "supporting_evidence": "",
  "reader_takeaway": ""
}

Rules — AVOID:
- generic observations ("AI is changing everything")
- motivational statements ("believe in yourself", "unlock your potential")
- obvious conclusions everyone already agrees with

Rules — PREFER:
- counterintuitive ideas
- lessons from experiments
- expert perspectives
- practical frameworks
- unique observations grounded in the provided research/memory

Constraints:
- Do not invent clients, metrics, quotes, or unverified personal achievements.
- supporting_evidence may reference research findings or verified experiences only.
- reader_takeaway must be actionable (a concrete next step the reader can try).
- common_belief and new_perspective must contrast each other.
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
