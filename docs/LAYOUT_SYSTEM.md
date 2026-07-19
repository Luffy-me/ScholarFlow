# Layout System

Layouts are JSON files under `design/layouts/`.

No hardcoded coordinates in engine code — the layout engine selects a JSON layout and reads regions.

## Layouts

- hero
- two_column
- three_column
- timeline
- architecture
- checklist
- comparison
- roadmap
- quote
- framework
- matrix

## Selection

`agents/layout_engine/` maps:

- role (Hook/CTA → hero)
- visual type (Timeline → timeline, Architecture → architecture, …)
- story type overrides

Each layout includes:

```json
{
  "id": "hero",
  "canvas": {"width": 1080, "height": 1350},
  "slots": ["heading", "visual", "footer"],
  "regions": {
    "heading": {"x": 64, "y": 80, "w": 952, "h": 220}
  }
}
```
