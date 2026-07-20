# Scene Graph

Every slide is JSON before any pixels are produced.

## Shape

```json
{
  "canvas": {"width": 1080, "height": 1350, "background": "#FFFFFF"},
  "elements": [
    {
      "id": "s1-heading",
      "type": "heading",
      "x": 64,
      "y": 80,
      "width": 952,
      "height": 120,
      "content": "...",
      "style": {},
      "meta": {}
    }
  ]
}
```

## Element types

Heading, text, icon, diagram, image, card, arrow, table, shape, metric, footer, bullet_list, callout, divider, progress

## Rules

- Scene Graph is canonical
- Renderers consume Scene Graph only
- Exporters may package SVG/PNG/PDF/PPTX/HTML but must not invent layout
- Future AI image generation plugs in as an optional element producer, not a renderer default

Schema: `schemas/scene_graph.py`  
Generator: `carousel/scene_graph_generator.py`
