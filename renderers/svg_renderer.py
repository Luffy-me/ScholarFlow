"""SVG Renderer — Scene Graph → pixel-precise SVG (no raster)."""

from __future__ import annotations

import html
from typing import Any

from schemas.scene_graph import SceneElement, SceneGraph, SlideScene


def _esc(text: str) -> str:
    return html.escape(text or "", quote=True)


class SVGRenderer:
    name = "svg_renderer"

    def render_slide(self, slide: SlideScene) -> str:
        w, h = slide.canvas.width, slide.canvas.height
        bg = slide.canvas.background
        parts = [
            f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}">',
            f'<rect width="100%" height="100%" fill="{_esc(bg)}"/>',
        ]
        for el in slide.elements:
            parts.append(self._render_element(el))
        parts.append("</svg>")
        return "\n".join(parts)

    def render_carousel(self, graph: SceneGraph) -> list[str]:
        return [self.render_slide(slide) for slide in graph.slides]

    def _render_element(self, el: SceneElement) -> str:
        fill = _esc(str(el.style.get("color") or "#111111"))
        accent = _esc(str(el.style.get("accent") or fill))
        x, y, w, h = el.x, el.y, el.width, el.height
        content = _esc(el.content)

        if el.type == "heading":
            size = int(el.style.get("font_size") or 44)
            return (
                f'<text x="{x}" y="{y + size}" width="{w}" '
                f'font-size="{size}" font-weight="700" fill="{fill}">'
                f"{content}</text>"
            )
        if el.type == "text":
            size = int(el.style.get("font_size") or 20)
            return f'<text x="{x}" y="{y + size}" font-size="{size}" fill="{fill}">{content}</text>'
        if el.type == "footer":
            size = int(el.style.get("font_size") or 12)
            return f'<text x="{x}" y="{y + size}" font-size="{size}" fill="{fill}">{content}</text>'
        if el.type == "icon":
            return (
                f'<g data-icon="{content}">'
                f'<circle cx="{x + w/2}" cy="{y + h/2}" r="{min(w, h)/2}" fill="none" stroke="{accent}" stroke-width="3"/>'
                f'<text x="{x + 8}" y="{y + h/2 + 5}" font-size="12" fill="{accent}">{content}</text>'
                f"</g>"
            )
        if el.type == "progress":
            current = int((el.meta or {}).get("current") or 1)
            total = max(1, int((el.meta or {}).get("total") or 1))
            pct = current / total
            return (
                f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="4" fill="#E5E7EB"/>'
                f'<rect x="{x}" y="{y}" width="{w * pct}" height="{h}" rx="4" fill="{accent}"/>'
            )
        if el.type == "bullet_list":
            items = (el.meta or {}).get("items") or content.split("\n")
            lines = [f'<g data-type="bullet_list" transform="translate({x},{y})">']
            for i, item in enumerate(items):
                yy = 28 + i * 48
                lines.append(f'<circle cx="8" cy="{yy - 6}" r="5" fill="{accent}"/>')
                lines.append(f'<text x="28" y="{yy}" font-size="22" fill="{fill}">{_esc(str(item))}</text>')
            lines.append("</g>")
            return "\n".join(lines)
        if el.type == "metric":
            label = _esc(str((el.meta or {}).get("label") or "Metric"))
            return (
                f'<g transform="translate({x},{y})">'
                f'<rect width="{w}" height="{h}" rx="16" fill="none" stroke="{accent}" stroke-width="2"/>'
                f'<text x="24" y="48" font-size="18" fill="{fill}">{label}</text>'
                f'<text x="24" y="100" font-size="28" font-weight="700" fill="{fill}">{content}</text>'
                f"</g>"
            )
        if el.type == "diagram":
            nodes = (el.meta or {}).get("nodes") or ["A", "B", "C"]
            lines = [
                f'<g data-type="diagram" transform="translate({x},{y})">',
                f'<rect width="{w}" height="{h}" rx="12" fill="none" stroke="{accent}" stroke-width="2"/>',
            ]
            for i, node in enumerate(nodes[:5]):
                nx = 40 + (i % 3) * min(280, w / 3)
                ny = 60 + (i // 3) * 120
                lines.append(
                    f'<rect x="{nx}" y="{ny}" width="200" height="64" rx="10" fill="none" stroke="{fill}" />'
                )
                lines.append(
                    f'<text x="{nx + 16}" y="{ny + 38}" font-size="18" fill="{fill}">{_esc(str(node))}</text>'
                )
                if i < min(4, len(nodes) - 1):
                    lines.append(
                        f'<line x1="{nx + 200}" y1="{ny + 32}" x2="{nx + min(280, w/3)}" y2="{ny + 32}" '
                        f'stroke="{accent}" stroke-width="2" marker-end="url(#arrow)" />'
                    )
            # Mermaid kept as metadata comment for exporters/plugins
            lines.append(f"<!-- mermaid\n{el.content}\n-->")
            lines.append("</g>")
            return "\n".join(lines)
        if el.type == "card":
            return (
                f'<g transform="translate({x},{y})">'
                f'<rect width="{w}" height="{h}" rx="16" fill="none" stroke="{fill}" />'
                f'<text x="20" y="40" font-size="20" fill="{fill}">{content}</text>'
                f"</g>"
            )
        if el.type == "shape":
            return f'<rect x="{x}" y="{y}" width="{w}" height="{h}" fill="none" stroke="{accent}" />'
        if el.type == "divider":
            return f'<line x1="{x}" y1="{y}" x2="{x + w}" y2="{y}" stroke="{fill}" stroke-width="2" />'
        # default text fallback
        return f'<text x="{x}" y="{y + 20}" font-size="16" fill="{fill}">{content}</text>'
