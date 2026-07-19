"""Layout Engine — select reusable JSON layouts (no hardcoded coordinates in code)."""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Any

from shared.knowledge import ROOT

LAYOUTS_DIR = ROOT / "design" / "layouts"

_VISUAL_TO_LAYOUT = {
    "Diagram": "framework",
    "Flowchart": "framework",
    "Timeline": "timeline",
    "Comparison": "comparison",
    "Table": "two_column",
    "Matrix": "matrix",
    "Architecture": "architecture",
    "Checklist": "checklist",
    "Cards": "three_column",
    "Quote": "quote",
    "Metrics": "three_column",
    "Illustration": "hero",
    "Roadmap": "roadmap",
    "Decision Tree": "two_column",
    "Mind Map": "architecture",
}

_ROLE_TO_LAYOUT = {
    "Hook": "hero",
    "CTA": "hero",
}


@lru_cache(maxsize=32)
def load_layout(layout_id: str) -> dict[str, Any]:
    path = LAYOUTS_DIR / f"{layout_id}.json"
    if not path.exists():
        path = LAYOUTS_DIR / "hero.json"
    with path.open(encoding="utf-8") as handle:
        data = json.load(handle)
    if not isinstance(data, dict):
        raise ValueError(f"Invalid layout JSON: {path}")
    return data


def list_layouts() -> list[str]:
    return sorted(p.stem for p in LAYOUTS_DIR.glob("*.json"))


class LayoutEngine:
    name = "layout_engine"

    def choose(self, *, role: str, visual_type: str, story_type: str = "") -> dict[str, Any]:
        layout_id = _ROLE_TO_LAYOUT.get(role) or _VISUAL_TO_LAYOUT.get(visual_type) or "hero"
        if story_type == "Architecture" and role not in {"Hook", "CTA"}:
            layout_id = "architecture"
        if story_type == "Checklist" and role not in {"Hook", "CTA"}:
            layout_id = "checklist"
        layout = dict(load_layout(layout_id))
        layout["selected_for"] = {"role": role, "visual_type": visual_type, "story_type": story_type}
        return layout
