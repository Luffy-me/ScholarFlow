"""Content Architect schemas."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


STORY_TYPES = [
    "Framework",
    "Case Study",
    "Timeline",
    "Comparison",
    "Checklist",
    "Roadmap",
    "Architecture",
    "Tutorial",
    "Before / After",
    "Problem → Solution",
    "Flywheel",
    "Decision Tree",
]


class ArchitectPlan(BaseModel):
    story_type: str
    audience: str
    goal: str
    slides: int = 8
    flow: list[str] = Field(default_factory=list)
    reading_level: str = "professional"
    objective: str = ""

    def as_dict(self) -> dict[str, Any]:
        return self.model_dump()
