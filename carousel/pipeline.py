"""Carousel Intelligence Pipeline — independent of the main post pipeline.

Research → Insight → Content Architect → Story Planner → Visual Planner →
Layout Engine → Diagram Engine → Scene Graph → SVG Renderer → Exporter
(+ Slide Reviewer)
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from agents.content_architect import ContentArchitect
from agents.diagram_engine import DiagramEngine
from agents.slide_reviewer import SlideReviewer
from agents.story_planner import StoryPlanner
from agents.visual_planner import VisualPlanner
from carousel.scene_graph_generator import SceneGraphGenerator
from export import ExportEngine
from renderers import SVGRenderer
from schemas.scene_graph import SceneGraph


class CarouselPipeline:
    """Deterministic carousel generation from topic (+ optional research/insight)."""

    def __init__(self) -> None:
        self.architect = ContentArchitect()
        self.story_planner = StoryPlanner()
        self.visual_planner = VisualPlanner()
        self.scene_gen = SceneGraphGenerator()
        self.diagrams = DiagramEngine()
        self.renderer = SVGRenderer()
        self.exporter = ExportEngine(self.renderer)
        self.reviewer = SlideReviewer()

    def run(
        self,
        *,
        topic: str,
        audience: str = "",
        goal: str = "",
        story_type: str | None = None,
        theme: str = "Minimal",
        insight: dict[str, Any] | None = None,
        research: dict[str, Any] | None = None,
        export_dir: str | Path | None = None,
        formats: list[str] | None = None,
    ) -> dict[str, Any]:
        architect = self.architect.plan(
            topic=topic,
            audience=audience,
            goal=goal,
            story_type=story_type,
            insight=insight,
            research=research,
        )
        story = self.story_planner.plan(architect, topic=topic)
        visuals = self.visual_planner.plan(story)
        graph = self.scene_gen.generate(story, visuals, theme=theme)
        review = self.reviewer.review(graph)
        svgs = self.renderer.render_carousel(graph)

        exports: dict[str, list[str]] = {}
        if export_dir is not None:
            exports = self.exporter.export(graph, export_dir, formats=formats)

        return {
            "architect": architect.as_dict(),
            "story": story.as_dict(),
            "visuals": [v.model_dump() for v in visuals],
            "scene_graph": graph.as_dict(),
            "svgs": svgs,
            "review": review.model_dump(),
            "exports": exports,
            "meta": {
                "theme": theme,
                "slide_count": len(graph.slides),
                "pipeline": "carousel_intelligence",
            },
        }

    def build_scene_graph(self, topic: str, **kwargs: Any) -> SceneGraph:
        result = self.run(topic=topic, **kwargs)
        return SceneGraph.model_validate(result["scene_graph"])
