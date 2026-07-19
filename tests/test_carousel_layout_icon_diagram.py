"""Layout, icon, and diagram engine tests."""

from __future__ import annotations

from agents.diagram_engine import DiagramEngine
from agents.icon_engine import LIBRARIES, IconEngine
from agents.layout_engine import LayoutEngine, list_layouts, load_layout


def test_layout_catalog_and_selection() -> None:
    layouts = list_layouts()
    assert "hero" in layouts
    assert "timeline" in layouts
    assert "architecture" in layouts
    engine = LayoutEngine()
    hero = engine.choose(role="Hook", visual_type="Quote")
    assert hero["id"] == "hero"
    assert "regions" in hero and "canvas" in hero
    arch = engine.choose(role="System Map", visual_type="Architecture", story_type="Architecture")
    assert arch["id"] == "architecture"
    # coordinates live in JSON, not code constants beyond ids
    assert "x" in next(iter(arch["regions"].values()))


def test_load_layout_json_has_no_code_coordinates_requirement() -> None:
    checklist = load_layout("checklist")
    assert checklist["slots"]
    assert checklist["canvas"]["width"] == 1080


def test_icon_engine_returns_library_ids() -> None:
    engine = IconEngine(library="lucide")
    icon = engine.select("Insight")
    assert icon.startswith("lucide:")
    assert ":" in icon
    many = engine.select_many(["Hook", "Problem", "CTA"])
    assert len(many) == 3
    for lib in LIBRARIES:
        assert IconEngine(library=lib).select("research").startswith(f"{lib}:")


def test_diagram_engine_mermaid_for_major_kinds() -> None:
    engine = DiagramEngine()
    for kind in (
        "Architecture",
        "Flowchart",
        "Sequence",
        "Timeline",
        "Mindmap",
        "Roadmap",
        "Decision Tree",
        "Comparison",
        "Matrix",
        "Cycle",
    ):
        spec = engine.build(kind, title=f"{kind} demo", labels=["A", "B", "C", "D"])
        assert spec.kind == kind
        assert spec.nodes
        assert isinstance(spec.mermaid, str) and spec.mermaid
        if kind not in {"Comparison", "Matrix"}:
            assert "-->" in spec.mermaid or "mindmap" in spec.mermaid or "->>" in spec.mermaid
