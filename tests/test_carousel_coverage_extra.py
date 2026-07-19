"""Additional carousel coverage to harden modular engines."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from agents.content_architect import ContentArchitect
from agents.diagram_engine import DiagramEngine
from agents.icon_engine import IconEngine
from agents.layout_engine import LayoutEngine, list_layouts
from agents.slide_reviewer import SlideReviewer
from agents.story_planner import StoryPlanner
from agents.visual_planner import VisualPlanner
from carousel import CarouselPipeline
from components import (
    BulletList,
    Callout,
    Card,
    DiagramPlaceholder,
    Divider,
    Footer,
    ImagePlaceholder,
    Paragraph,
    Table,
)
from export import ExportEngine
from renderers import SVGRenderer
from schemas.scene_graph import Canvas, SceneElement, SlideScene


@pytest.mark.parametrize(
    "story_type",
    [
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
    ],
)
def test_all_story_types_produce_flow(story_type: str) -> None:
    plan = ContentArchitect().plan(topic="sample topic", story_type=story_type)
    assert plan.story_type == story_type
    assert plan.flow[0] == "Hook"
    assert plan.flow[-1] == "CTA"


@pytest.mark.parametrize(
    "theme",
    ["Apple", "Stripe", "Linear", "Anthropic", "OpenAI", "Notion", "Minimal", "Dark"],
)
def test_all_themes_render_svg(theme: str) -> None:
    result = CarouselPipeline().run(topic="theme check", theme=theme, story_type="Checklist")
    assert result["scene_graph"]["theme"] == theme
    assert result["svgs"][0].startswith("<svg")


def test_run_accepts_insight_and_research_context() -> None:
    result = CarouselPipeline().run(
        topic="retrieval quality",
        insight={
            "hidden_pattern": "questions beat context stuffing",
            "contrarian_view": "less context",
        },
        research={"evidence": [{"claim": "tighter questions help", "verified": True}]},
        theme="OpenAI",
    )
    assert result["architect"]["story_type"] in {
        "Framework",
        "Problem → Solution",
        "Architecture",
    }
    assert result["review"]["slides"]


def test_export_engine_writes_scene_graph_sidecar(tmp_path: Path) -> None:
    graph = CarouselPipeline().build_scene_graph(topic="export sidecar")
    written = ExportEngine().export(graph, tmp_path, formats=["svg"])
    assert written["svg"]
    data = json.loads((tmp_path / "scene_graph.json").read_text(encoding="utf-8"))
    assert data["topic"] == "export sidecar"


def test_svg_renderer_handles_core_element_types() -> None:
    slide = SlideScene(
        slide_number=1,
        role="Hook",
        layout_id="hero",
        canvas=Canvas(width=1080, height=1350, background="#FFFFFF"),
        elements=[
            SceneElement(
                id="h",
                type="heading",
                x=10,
                y=10,
                width=100,
                height=40,
                content="Hi",
                style={"color": "#111"},
            ),
            SceneElement(id="t", type="text", x=10, y=60, width=100, height=40, content="Body"),
            SceneElement(id="i", type="icon", x=10, y=100, width=40, height=40, content="lucide:star"),
            SceneElement(id="d", type="divider", x=10, y=160, width=200, height=2),
            SceneElement(id="s", type="shape", x=10, y=180, width=50, height=50),
            SceneElement(id="c", type="card", x=10, y=250, width=200, height=100, content="Card"),
            SceneElement(
                id="p",
                type="progress",
                x=10,
                y=5,
                width=200,
                height=6,
                meta={"current": 1, "total": 5},
                style={"accent": "#00f"},
            ),
        ],
    )
    svg = SVGRenderer().render_slide(slide)
    assert 'data-icon="lucide:star"' in svg
    assert "Card" in svg


def test_components_cover_library() -> None:
    assert Paragraph("p").type == "text"
    assert BulletList(["a", "b"]).props["items"] == ["a", "b"]
    assert Callout("note").props["variant"] == "info"
    assert Card("body", title="T").props["title"] == "T"
    assert Table(["A"], [["1"]]).type == "table"
    assert Divider().type == "divider"
    assert ImagePlaceholder("img").props["placeholder"] is True
    assert DiagramPlaceholder("flowchart TD", kind="Flowchart").type == "diagram"
    assert Footer("f").type == "footer"


def test_layout_engine_maps_visual_types() -> None:
    engine = LayoutEngine()
    assert engine.choose(role="Body", visual_type="Timeline")["id"] == "timeline"
    assert engine.choose(role="Body", visual_type="Matrix")["id"] == "matrix"
    assert engine.choose(role="Body", visual_type="Checklist")["id"] == "checklist"
    assert engine.choose(role="Body", visual_type="Roadmap")["id"] == "roadmap"
    assert engine.choose(role="CTA", visual_type="Illustration")["id"] == "hero"


def test_icon_alias_and_unknown_fallback() -> None:
    engine = IconEngine()
    assert engine.select("hook").endswith("sparkles")
    assert ":" in engine.select("unknown-concept-xyz")


def test_diagram_cycle_closes_loop() -> None:
    spec = DiagramEngine().build("Cycle", title="Loop", labels=["A", "B", "C"])
    assert any(e == ["C", "A"] for e in spec.edges)


def test_slide_reviewer_flags_long_heading() -> None:
    slide = SlideScene(
        slide_number=1,
        role="Hook",
        elements=[
            SceneElement(
                id="h",
                type="heading",
                x=0,
                y=0,
                width=1000,
                height=100,
                content="X" * 120,
                style={"color": "#111"},
            )
        ],
    )
    review = SlideReviewer().review_slide(slide)
    assert review.readability < 80
    assert any("heading" in r.lower() for r in review.recommendations)


def test_story_visual_alignment_lengths() -> None:
    for story_type in ("Timeline", "Comparison", "Checklist"):
        architect = ContentArchitect().plan(topic="t", story_type=story_type)
        story = StoryPlanner().plan(architect, topic="t")
        visuals = VisualPlanner().plan(story)
        assert len(visuals) == len(story.slides)


def test_design_files_exist() -> None:
    root = Path("design")
    for name in ("colors.json", "spacing.json", "typography.json", "icons.json", "themes.json"):
        assert (root / name).exists()
    assert len(list_layouts()) >= 10
