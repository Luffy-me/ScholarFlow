"""Story Planner schemas."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class SlideOutline(BaseModel):
    slide_number: int
    role: str
    title: str = ""
    summary: str = ""
    key_points: list[str] = Field(default_factory=list)

    def as_dict(self) -> dict[str, Any]:
        return self.model_dump()


class StoryPlan(BaseModel):
    topic: str
    story_type: str
    slides: list[SlideOutline] = Field(default_factory=list)

    def as_dict(self) -> dict[str, Any]:
        return self.model_dump()
