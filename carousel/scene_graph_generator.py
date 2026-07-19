"""Scene Graph Generator — compose slide scenes from plans (no rendering)."""

from __future__ import annotations

import json
from functools import lru_cache
from typing import Any

from agents.diagram_engine import DiagramEngine
from agents.icon_engine import IconEngine
from agents.layout_engine import LayoutEngine
from agents.story_planner.schemas import StoryPlan
from agents.visual_planner.schemas import SlideVisualPlan
from schemas.scene_graph import Canvas, SceneElement, SceneGraph, SlideScene
from shared.knowledge import ROOT


@lru_cache(maxsize=1)
def _themes() -> dict[str, Any]:
    path = ROOT / "design" / "themes.json"
    with path.open(encoding="utf-8") as handle:
        data = json.load(handle)
    return data if isinstance(data, dict) else {}


class SceneGraphGenerator:
    name = "scene_graph_generator"

    def __init__(self) -> None:
        self.layouts = LayoutEngine()
        self.icons = IconEngine()
        self.diagrams = DiagramEngine()

    def generate(
        self,
        story: StoryPlan,
        visuals: list[SlideVisualPlan],
        *,
        theme: str = "Minimal",
    ) -> SceneGraph:
        theme_tokens = _themes().get(theme) or _themes().get("Minimal") or {}
        bg = str(theme_tokens.get("bg") or "#FFFFFF")
        fg = str(theme_tokens.get("fg") or "#111111")
        accent = str(theme_tokens.get("accent") or "#111111")

        visual_by_slide = {v.slide_number: v for v in visuals}
        slides: list[SlideScene] = []
        total = len(story.slides)

        for outline in story.slides:
            visual = visual_by_slide.get(outline.slide_number)
            visual_type = visual.visual.type if visual else "Diagram"
            layout = self.layouts.choose(
                role=outline.role,
                visual_type=visual_type,
                story_type=story.story_type,
            )
            canvas_cfg = layout.get("canvas") or {"width": 1080, "height": 1350}
            regions = layout.get("regions") or {}
            elements: list[SceneElement] = []

            heading_region = regions.get("heading") or regions.get("eyebrow") or {
                "x": 64, "y": 80, "w": 952, "h": 120
            }
            elements.append(
                SceneElement(
                    id=f"s{outline.slide_number}-heading",
                    type="heading",
                    x=heading_region["x"],
                    y=heading_region["y"],
                    width=heading_region["w"],
                    height=heading_region["h"],
                    content=outline.title,
                    style={"color": fg, "font_size": 44, "weight": 700},
                )
            )

            icon_id = self.icons.select(outline.role)
            elements.append(
                SceneElement(
                    id=f"s{outline.slide_number}-icon",
                    type="icon",
                    x=64,
                    y=heading_region["y"] + heading_region["h"] + 12,
                    width=48,
                    height=48,
                    content=icon_id,
                    style={"color": accent},
                    meta={"icon_id": icon_id},
                )
            )

            # Body / visual region
            body_key = next(
                (k for k in ("visual", "diagram", "items", "steps", "rail", "phases", "grid", "left", "quote") if k in regions),
                None,
            )
            body = regions.get(body_key) if body_key else {"x": 64, "y": 280, "w": 952, "h": 800}
            points = outline.key_points or [outline.summary]
            if visual_type in {"Checklist", "Cards"}:
                elements.append(
                    SceneElement(
                        id=f"s{outline.slide_number}-bullets",
                        type="bullet_list",
                        x=body["x"],
                        y=body["y"],
                        width=body["w"],
                        height=body["h"],
                        content="\n".join(points),
                        style={"color": fg, "font_size": 22},
                        meta={"items": points},
                    )
                )
            elif visual_type in {"Metrics"}:
                for i, point in enumerate(points[:3]):
                    elements.append(
                        SceneElement(
                            id=f"s{outline.slide_number}-metric-{i}",
                            type="metric",
                            x=body["x"] + i * 320,
                            y=body["y"],
                            width=280,
                            height=180,
                            content=point,
                            style={"color": fg, "accent": accent},
                            meta={"label": f"Signal {i+1}"},
                        )
                    )
            else:
                diagram = self.diagrams.build(
                    "Architecture"
                    if visual_type == "Architecture"
                    else "Timeline"
                    if visual_type == "Timeline"
                    else "Decision Tree"
                    if visual_type == "Decision Tree"
                    else "Mindmap"
                    if visual_type == "Mind Map"
                    else "Comparison"
                    if visual_type == "Comparison"
                    else "Matrix"
                    if visual_type == "Matrix"
                    else "Roadmap"
                    if visual_type == "Roadmap"
                    else "Flowchart",
                    title=outline.title,
                    labels=points,
                )
                elements.append(
                    SceneElement(
                        id=f"s{outline.slide_number}-diagram",
                        type="diagram",
                        x=body["x"],
                        y=body["y"],
                        width=body["w"],
                        height=min(body["h"], 700),
                        content=diagram.mermaid,
                        style={"color": fg, "accent": accent},
                        meta={"kind": diagram.kind, "nodes": diagram.nodes},
                    )
                )

            footer_region = regions.get("footer") or {"x": 64, "y": 1260, "w": 952, "h": 40}
            elements.append(
                SceneElement(
                    id=f"s{outline.slide_number}-footer",
                    type="footer",
                    x=footer_region["x"],
                    y=footer_region["y"],
                    width=footer_region["w"],
                    height=footer_region["h"],
                    content=f"{story.topic} · {outline.slide_number}/{total}",
                    style={"color": theme_tokens.get("muted") or "#666666", "font_size": 12},
                )
            )
            elements.append(
                SceneElement(
                    id=f"s{outline.slide_number}-progress",
                    type="progress",
                    x=64,
                    y=40,
                    width=952,
                    height=8,
                    content=f"{outline.slide_number}/{total}",
                    style={"color": accent},
                    meta={"current": outline.slide_number, "total": total},
                )
            )

            slides.append(
                SlideScene(
                    slide_number=outline.slide_number,
                    role=outline.role,
                    layout_id=str(layout.get("id") or "hero"),
                    visual_type=visual_type,
                    canvas=Canvas(
                        width=int(canvas_cfg.get("width", 1080)),
                        height=int(canvas_cfg.get("height", 1350)),
                        background=bg,
                    ),
                    elements=elements,
                )
            )

        return SceneGraph(
            topic=story.topic,
            theme=theme,
            story_type=story.story_type,
            slides=slides,
            meta={"generator": self.name, "slide_count": total},
        )
