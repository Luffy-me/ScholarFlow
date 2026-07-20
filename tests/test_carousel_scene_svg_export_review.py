"""Scene graph, SVG render, export, and slide review tests."""

from __future__ import annotations

from pathlib import Path

from agents.content_architect import ContentArchitect
from agents.slide_reviewer import SlideReviewer
from agents.story_planner import StoryPlanner
from agents.visual_planner import VisualPlanner
from carousel import CarouselPipeline, SceneGraphGenerator
from components import COMPONENT_TYPES, Heading, Metric, ProgressIndicator
from export import ExportEngine
from renderers import SVGRenderer
from schemas.scene_graph import SceneGraph


def test_component_library_reusable() -> None:
    assert "Heading" in COMPONENT_TYPES
    h = Heading("Title", level=1)
    assert h.type == "heading"
    m = Metric("Latency", "120ms")
    assert m.props["label"] == "Latency"
    p = ProgressIndicator(2, 8)
    assert p.props["current"] == 2


def test_scene_graph_created_before_render() -> None:
    architect = ContentArchitect().plan(topic="eval harness", story_type="Framework")
    story = StoryPlanner().plan(architect, topic="eval harness")
    visuals = VisualPlanner().plan(story)
    graph = SceneGraphGenerator().generate(story, visuals, theme="Stripe")
    assert isinstance(graph, SceneGraph)
    assert graph.slides
    assert all(s.canvas.width == 1080 and s.canvas.height == 1350 for s in graph.slides)
    assert all(s.elements for s in graph.slides)
    # nothing rendered yet in scene graph
    blob = graph.as_dict()
    assert "svg" not in blob


def test_svg_renderer_is_vector_only() -> None:
    result = CarouselPipeline().run(topic="local models", theme="Minimal")
    svgs = result["svgs"]
    assert len(svgs) == result["meta"]["slide_count"]
    for svg in svgs:
        assert svg.startswith("<svg")
        assert "xmlns=" in svg
        assert "<img" not in svg.lower()
        assert "base64" not in svg.lower()


def test_export_formats_from_scene_graph(tmp_path: Path) -> None:
    pipe = CarouselPipeline()
    result = pipe.run(
        topic="RAG architecture",
        story_type="Architecture",
        theme="Linear",
        export_dir=tmp_path,
        formats=["svg", "png", "pdf", "pptx", "html"],
    )
    exports = result["exports"]
    assert exports["svg"]
    assert exports["html"]
    assert exports["png"]
    assert exports["pdf"]
    assert exports["pptx"]
    assert (tmp_path / "scene_graph.json").exists()
    assert Path(exports["svg"][0]).read_text(encoding="utf-8").startswith("<svg")
    assert Path(exports["png"][0]).read_bytes()[:8] == b"\x89PNG\r\n\x1a\n"
    assert Path(exports["pptx"][0]).read_bytes()[:2] == b"PK"


def test_slide_reviewer_scores_and_recommendations() -> None:
    graph = CarouselPipeline().build_scene_graph(topic="decision making", story_type="Decision Tree")
    review = SlideReviewer().review(graph)
    assert review.slides
    for slide in review.slides:
        for key in (
            "readability",
            "whitespace",
            "balance",
            "hierarchy",
            "visual_density",
            "accessibility",
            "consistency",
            "overall",
        ):
            assert 0 <= getattr(slide, key) <= 100
        assert slide.recommendations
    assert 0 <= review.overall <= 100


def test_carousel_pipeline_end_to_end_deterministic() -> None:
    pipe = CarouselPipeline()
    a = pipe.run(topic="flywheel growth loops", story_type="Flywheel", theme="Notion")
    b = pipe.run(topic="flywheel growth loops", story_type="Flywheel", theme="Notion")
    assert a["architect"] == b["architect"]
    assert a["scene_graph"]["story_type"] == "Flywheel"
    assert len(a["svgs"]) == a["architect"]["slides"]


def test_themes_supported_in_design_system() -> None:
    from carousel.scene_graph_generator import _themes

    themes = _themes()
    for name in ("Apple", "Stripe", "Linear", "Anthropic", "OpenAI", "Notion", "Minimal", "Dark"):
        assert name in themes
