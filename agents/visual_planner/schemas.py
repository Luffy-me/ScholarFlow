"""Visual Planner schemas."""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field

VisualType = Literal[
    "Diagram",
    "Flowchart",
    "Timeline",
    "Comparison",
    "Table",
    "Matrix",
    "Architecture",
    "Checklist",
    "Cards",
    "Quote",
    "Metrics",
    "Illustration",
    "Roadmap",
    "Decision Tree",
    "Mind Map",
]

Priority = Literal["primary", "secondary", "supporting"]


class VisualPlan(BaseModel):
    type: str
    reason: str
    priority: str = "primary"

    def as_dict(self) -> dict[str, Any]:
        return self.model_dump()


class SlideVisualPlan(BaseModel):
    slide_number: int
    role: str
    visual: VisualPlan
    elements_hint: list[str] = Field(default_factory=list)
