# Carousel Intelligence Engine

Independent module. Does **not** generate slides directly — it thinks first.

## Pipeline

```text
Research / Insight (inputs)
  ↓
Content Architect
  ↓
Story Planner
  ↓
Visual Planner
  ↓
Layout Engine
  ↓
Diagram Engine
  ↓
Scene Graph Generator
  ↓
SVG Renderer
  ↓
Exporter
(+ Slide Reviewer)
```

## Entry point

```python
from carousel import CarouselPipeline

result = CarouselPipeline().run(
    topic="local LLM evaluation loops",
    story_type="Framework",
    theme="Stripe",
    export_dir="out/carousel",
)
```

## Rules

- No UI / React / HTML-first rendering
- No AI image generation by default (optional future plugin)
- Scene Graph is the source of truth
- Rendering happens only at export
- Outputs are deterministic

## Packages

| Path | Role |
|---|---|
| `agents/content_architect/` | Story type, audience, flow |
| `agents/story_planner/` | Slide outline |
| `agents/visual_planner/` | Visual type per slide |
| `agents/layout_engine/` | JSON layout selection |
| `agents/icon_engine/` | Icon IDs only |
| `agents/diagram_engine/` | Diagram + Mermaid |
| `agents/slide_reviewer/` | Design QA scores |
| `schemas/scene_graph.py` | Structured scenes |
| `renderers/svg_renderer.py` | Vector render |
| `export/` | SVG/PNG/PDF/PPTX/HTML |
| `design/` | Tokens + layouts |
| `components/` | Reusable content components |
