"""Slide Reviewer — score readability/balance/hierarchy without rendering UI."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field

from schemas.scene_graph import SceneGraph, SlideScene
from shared.quality import clamp_score


class SlideReview(BaseModel):
    slide_number: int
    readability: int = 0
    whitespace: int = 0
    balance: int = 0
    hierarchy: int = 0
    visual_density: int = 0
    accessibility: int = 0
    consistency: int = 0
    overall: int = 0
    recommendations: list[str] = Field(default_factory=list)


class CarouselReview(BaseModel):
    slides: list[SlideReview] = Field(default_factory=list)
    overall: int = 0
    recommendations: list[str] = Field(default_factory=list)


class SlideReviewer:
    name = "slide_reviewer"

    def review_slide(self, slide: SlideScene, *, theme: str = "Minimal") -> SlideReview:
        recommendations: list[str] = []
        texts = [e for e in slide.elements if e.type in {"heading", "text", "bullet_list", "footer"}]
        visuals = [e for e in slide.elements if e.type in {"diagram", "icon", "metric", "card"}]
        heading = next((e for e in slide.elements if e.type == "heading"), None)

        readability = 80
        if heading and len(heading.content) > 90:
            readability -= 20
            recommendations.append("Shorten the heading for faster scanning.")
        if any(e.type == "text" and len(e.content) > 280 for e in slide.elements):
            readability -= 15
            recommendations.append("Reduce paragraph length; prefer bullets or diagram labels.")

        # Whitespace: penalize too many elements
        whitespace = clamp_score(90 - max(0, len(slide.elements) - 8) * 8)
        if whitespace < 60:
            recommendations.append("Increase whitespace by removing secondary elements.")

        balance = 75
        left = [e for e in slide.elements if e.x < slide.canvas.width / 2]
        right = [e for e in slide.elements if e.x >= slide.canvas.width / 2]
        if abs(len(left) - len(right)) > 4 and slide.layout_id in {"two_column", "comparison"}:
            balance -= 20
            recommendations.append("Balance left/right visual weight.")

        hierarchy = 85 if heading else 40
        if heading and any(e.type == "heading" and e is not heading for e in slide.elements):
            hierarchy -= 15
            recommendations.append("Keep a single dominant heading.")

        density = clamp_score(100 - len(slide.elements) * 6)
        if density < 50:
            recommendations.append("Lower visual density; one primary visual per slide.")

        accessibility = 70
        bg = (slide.canvas.background or "").lower()
        fg_colors = [str(e.style.get("color", "")).lower() for e in texts]
        if bg in {"#ffffff", "#fff", "#f5f5f7"} and any(c in {"#ffffff", "#f8fafc"} for c in fg_colors):
            accessibility -= 30
            recommendations.append("Improve contrast between text and background.")
        if not any(e.type == "footer" for e in slide.elements):
            accessibility -= 5

        consistency = 80
        if not any(e.type == "progress" for e in slide.elements):
            consistency -= 10
            recommendations.append("Add a progress indicator for carousel consistency.")

        overall = clamp_score(
            (
                readability
                + whitespace
                + balance
                + hierarchy
                + density
                + accessibility
                + consistency
            )
            / 7
        )
        if not recommendations:
            recommendations.append("Solid slide — keep hierarchy and one primary visual.")

        return SlideReview(
            slide_number=slide.slide_number,
            readability=readability,
            whitespace=whitespace,
            balance=balance,
            hierarchy=hierarchy,
            visual_density=density,
            accessibility=accessibility,
            consistency=consistency,
            overall=overall,
            recommendations=recommendations,
        )

    def review(self, graph: SceneGraph) -> CarouselReview:
        slides = [self.review_slide(s, theme=graph.theme) for s in graph.slides]
        overall = clamp_score(sum(s.overall for s in slides) / max(1, len(slides)))
        global_recs: list[str] = []
        if overall < 70:
            global_recs.append("Revise weak slides before export.")
        if len({s.layout_id for s in graph.slides}) == 1 and len(graph.slides) > 4:
            global_recs.append("Vary layouts across the deck to avoid monotony.")
        return CarouselReview(slides=slides, overall=overall, recommendations=global_recs)
