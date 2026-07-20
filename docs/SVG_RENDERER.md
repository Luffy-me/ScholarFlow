# SVG Renderer

`renderers/svg_renderer.py`

## Flow

```text
Scene Graph → SVG
```

## Guarantees

- Vector only (no raster embeds)
- Deterministic output for a given Scene Graph
- Per-slide SVG strings
- Diagram Mermaid kept as SVG comments + node shapes drawn as vectors

## Non-goals

- No React
- No browser HTML layout engine
- No AI image generation

PNG/PDF/PPTX packaging is handled by `export/` and treats SVG/Scene Graph as source of truth.
