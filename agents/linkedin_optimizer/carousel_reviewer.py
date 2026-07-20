"""Carousel review for the LinkedIn optimizer layer (does not replace SlideReviewer)."""

from __future__ import annotations

from typing import Any

from agents.linkedin_optimizer._text import clamp01, clamp100, mean
from agents.linkedin_optimizer.schemas import CarouselReviewReport


class CarouselReviewer:
    """Review carousel plans/scene graphs for LinkedIn feed fitness.

    If an existing SlideReviewer/CarouselReview dict is provided, we enrich it.
    We do not regenerate slides or replace the carousel subsystem.
    """

    name = "linkedin_carousel_reviewer"

    def review(
        self,
        carousel: Any | None = None,
        *,
        existing_review: dict[str, Any] | None = None,
    ) -> CarouselReviewReport:
        if carousel is None and not existing_review:
            return CarouselReviewReport(
                recommendations=["No carousel payload provided — skipped carousel review."],
            )

        # Prefer existing review signals when present (no duplication of slide_reviewer work)
        if existing_review:
            return self._from_existing(existing_review)

        # SceneGraph-like object/dict
        slides = self._slides(carousel)
        slide_count = len(slides)
        if slide_count == 0:
            return CarouselReviewReport(recommendations=["Carousel contained zero slides."])

        densities: list[float] = []
        hierarchies: list[float] = []
        loads: list[float] = []
        for slide in slides:
            elements = self._elements(slide)
            text_len = sum(len(str(e.get("content") or "")) for e in elements)
            densities.append(clamp01(1.0 - max(0, len(elements) - 8) * 0.08))
            has_heading = any(e.get("type") == "heading" for e in elements)
            hierarchies.append(0.85 if has_heading else 0.4)
            loads.append(clamp01(1.0 - max(0, text_len - 220) / 400))

        slide_density = mean(densities)
        visual_hierarchy = mean(hierarchies)
        information_load = mean(loads)
        narrative_flow = clamp01(0.4 + 0.08 * min(slide_count, 8))
        if slide_count < 4:
            narrative_flow -= 0.15
        if slide_count > 12:
            narrative_flow -= 0.2
        transitions = clamp01(0.55 + (0.2 if 6 <= slide_count <= 10 else 0.0))
        consistency = 0.7
        roles = [str(s.get("role") or s.get("layout_id") or "") for s in slides]
        if len(set(roles)) >= min(3, slide_count):
            consistency += 0.15

        overall = mean(
            [slide_density, visual_hierarchy, narrative_flow, information_load, transitions, consistency]
        )
        recs: list[str] = []
        if slide_density < 0.55:
            recs.append("Reduce slide density — one primary idea per slide.")
        if visual_hierarchy < 0.6:
            recs.append("Strengthen visual hierarchy with a single dominant heading.")
        if information_load < 0.55:
            recs.append("Lower information load; move detail off-slide or into later slides.")
        if not (6 <= slide_count <= 10):
            recs.append("Ideal LinkedIn carousel length is typically 6–10 slides.")
        if narrative_flow < 0.55:
            recs.append("Improve narrative flow: hook → tension → framework → takeaway.")

        return CarouselReviewReport(
            slide_density=round(clamp01(slide_density), 4),
            visual_hierarchy=round(clamp01(visual_hierarchy), 4),
            narrative_flow=round(clamp01(narrative_flow), 4),
            information_load=round(clamp01(information_load), 4),
            transitions=round(clamp01(transitions), 4),
            consistency=round(clamp01(consistency), 4),
            overall=round(clamp01(overall), 4),
            recommendations=recs,
            slide_count=slide_count,
        )

    def _from_existing(self, review: dict[str, Any]) -> CarouselReviewReport:
        overall = float(review.get("overall") or 0) / 100.0
        slides = review.get("slides") or []
        recs = list(review.get("recommendations") or [])
        dens = mean([float(s.get("visual_density") or 0) / 100 for s in slides if isinstance(s, dict)]) or overall
        hier = mean([float(s.get("hierarchy") or 0) / 100 for s in slides if isinstance(s, dict)]) or overall
        return CarouselReviewReport(
            slide_density=round(clamp01(dens), 4),
            visual_hierarchy=round(clamp01(hier), 4),
            narrative_flow=round(clamp01(overall), 4),
            information_load=round(clamp01(overall), 4),
            transitions=round(clamp01(overall), 4),
            consistency=round(
                clamp01(
                    mean([float(s.get("consistency") or 0) / 100 for s in slides if isinstance(s, dict)]) or overall
                ),
                4,
            ),
            overall=round(clamp01(overall), 4),
            recommendations=recs
            or ["Using existing carousel review signals from SlideReviewer."],
            slide_count=len(slides),
        )

    def _slides(self, carousel: Any) -> list[dict[str, Any]]:
        if hasattr(carousel, "slides"):
            slides = carousel.slides
            out = []
            for s in slides:
                if hasattr(s, "model_dump"):
                    out.append(s.model_dump())
                elif isinstance(s, dict):
                    out.append(s)
            return out
        if isinstance(carousel, dict):
            return [s for s in (carousel.get("slides") or []) if isinstance(s, dict)]
        if isinstance(carousel, list):
            return [s if isinstance(s, dict) else {} for s in carousel]
        return []

    def _elements(self, slide: dict[str, Any]) -> list[dict[str, Any]]:
        els = slide.get("elements") or []
        return [e if isinstance(e, dict) else {} for e in els]
