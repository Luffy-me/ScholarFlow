"""Prompts for optional LLM enrichment of writing-quality analysis.

Core detection is deterministic. LLM output may refine improvements only.
Never ask the model to label authorship as AI or human.
"""

from __future__ import annotations

import json
from typing import Any


SYSTEM_PROMPT = """You are a LinkedIn writing-quality analyst.

Your job is to evaluate whether content contains patterns commonly associated
with low-quality AI writing.

CRITICAL RULES:
- Do NOT claim the content was written by AI.
- Do NOT claim the content was written by a human.
- Evaluate pattern risk and authenticity signals only.
- Prefer concrete improvements over vague advice.

Return JSON with:
{
  "improvements": ["..."]
}
"""


def build_enrichment_user_prompt(
    *,
    content: str,
    content_mode: str,
    detected_patterns: list[dict[str, Any]],
    preferred_hits: list[str],
) -> str:
    return (
        "Draft:\n"
        f"{content}\n\n"
        f"Content mode: {content_mode or 'founder'}\n"
        f"Detected pattern categories: {json.dumps(detected_patterns)}\n"
        f"Preferred human-pattern signals found: {json.dumps(preferred_hits)}\n\n"
        "Suggest 2-5 concrete improvements that remove low-quality AI writing patterns "
        "without inventing experiences, metrics, clients, or emotions."
    )
