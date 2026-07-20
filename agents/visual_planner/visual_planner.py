"""Visual Planner — decide what visual explains each slide (not the text)."""

from __future__ import annotations

from agents.story_planner.schemas import StoryPlan
from agents.visual_planner.schemas import SlideVisualPlan, VisualPlan


_ROLE_VISUALS: dict[str, tuple[str, str, str]] = {
    "Hook": ("Quote", "A short tension line beats a paragraph wall", "primary"),
    "Problem": ("Cards", "Separate pain points into scannable cards", "primary"),
    "Research": ("Table", "Evidence is clearer as structured rows", "primary"),
    "Insight": ("Diagram", "Show the hidden relationship, not a slogan", "primary"),
    "Framework": ("Flowchart", "Named steps need directional flow", "primary"),
    "Example": ("Metrics", "Concrete numbers/outcomes ground the claim", "secondary"),
    "Mistakes": ("Checklist", "Avoidance guidance works as checks", "primary"),
    "CTA": ("Illustration", "Leave space; one action, one question", "supporting"),
    "Context": ("Cards", "Set scene with compact context cards", "secondary"),
    "Challenge": ("Comparison", "Before-state vs desired-state contrast", "primary"),
    "Approach": ("Architecture", "Method is a system map", "primary"),
    "Results": ("Metrics", "Outcomes belong in metric blocks", "primary"),
    "Timeline": ("Timeline", "Sequence needs a temporal rail", "primary"),
    "Origin": ("Timeline", "Start of the rail", "secondary"),
    "Option A": ("Comparison", "Side-by-side evaluation", "primary"),
    "Option B": ("Comparison", "Side-by-side evaluation", "primary"),
    "Decision Matrix": ("Matrix", "Criteria × options grid", "primary"),
    "Phase 1": ("Roadmap", "Phased delivery map", "primary"),
    "Phase 2": ("Roadmap", "Phased delivery map", "primary"),
    "Phase 3": ("Roadmap", "Phased delivery map", "primary"),
    "System Map": ("Architecture", "Components and boundaries", "primary"),
    "Data Flow": ("Flowchart", "Directional movement of data", "primary"),
    "Question": ("Decision Tree", "Branching choice visual", "primary"),
    "Branch A": ("Decision Tree", "Left path", "secondary"),
    "Branch B": ("Decision Tree", "Right path", "secondary"),
    "Loop overview": ("Mind Map", "Circular reinforcing loop", "primary"),
}


class VisualPlanner:
    name = "visual_planner"

    def plan(self, story: StoryPlan) -> list[SlideVisualPlan]:
        plans: list[SlideVisualPlan] = []
        for slide in story.slides:
            vtype, reason, priority = _ROLE_VISUALS.get(
                slide.role,
                ("Diagram", f"Default explanatory visual for {slide.role}", "primary"),
            )
            # Story-type overrides
            if story.story_type == "Architecture" and slide.role in {"Framework", "Insight", "Approach"}:
                vtype, reason = "Architecture", "Architecture stories prefer system maps"
            if story.story_type == "Timeline" and slide.role not in {"Hook", "CTA"}:
                vtype, reason = "Timeline", "Timeline stories keep temporal visuals"
            if story.story_type == "Comparison" and slide.role not in {"Hook", "CTA"}:
                vtype, reason = "Comparison", "Comparison stories stay side-by-side"
            plans.append(
                SlideVisualPlan(
                    slide_number=slide.slide_number,
                    role=slide.role,
                    visual=VisualPlan(type=vtype, reason=reason, priority=priority),
                    elements_hint=[vtype.lower(), "heading", "footer"],
                )
            )
        return plans
