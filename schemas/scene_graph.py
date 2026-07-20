"""Scene Graph — structured slide representation before any rendering."""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field

ElementType = Literal[
    "heading",
    "text",
    "icon",
    "diagram",
    "image",
    "card",
    "arrow",
    "table",
    "shape",
    "metric",
    "footer",
    "bullet_list",
    "callout",
    "divider",
    "progress",
]


class Canvas(BaseModel):
    width: int = 1080
    height: int = 1350
    background: str = "#FFFFFF"


class SceneElement(BaseModel):
    id: str
    type: ElementType
    x: float
    y: float
    width: float
    height: float
    content: str = ""
    style: dict[str, Any] = Field(default_factory=dict)
    meta: dict[str, Any] = Field(default_factory=dict)


class SlideScene(BaseModel):
    slide_number: int
    role: str = ""
    layout_id: str = "hero"
    visual_type: str = ""
    canvas: Canvas = Field(default_factory=Canvas)
    elements: list[SceneElement] = Field(default_factory=list)

    def as_dict(self) -> dict[str, Any]:
        return self.model_dump()


class SceneGraph(BaseModel):
    """Full carousel as structured scenes — nothing rendered yet."""

    topic: str = ""
    theme: str = "Minimal"
    story_type: str = ""
    slides: list[SlideScene] = Field(default_factory=list)
    meta: dict[str, Any] = Field(default_factory=dict)

    def as_dict(self) -> dict[str, Any]:
        return self.model_dump()
