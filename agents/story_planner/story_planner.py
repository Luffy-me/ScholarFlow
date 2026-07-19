"""Story Planner — slide-by-slide narrative outline."""

from __future__ import annotations

from agents.content_architect.schemas import ArchitectPlan
from agents.story_planner.schemas import SlideOutline, StoryPlan


_ROLE_TEMPLATES: dict[str, tuple[str, list[str]]] = {
    "Hook": ("A sharp opening tension", ["One concrete observation", "Why the reader should care"]),
    "Problem": ("The costly default", ["What breaks today", "Who feels the pain"]),
    "Research": ("What the evidence shows", ["Signal from sources", "Pattern across discussions"]),
    "Insight": ("The non-obvious takeaway", ["Hidden pattern", "Why common advice fails"]),
    "Framework": ("A usable mental model", ["Named steps", "How pieces connect"]),
    "Example": ("Proof in practice", ["Specific scenario", "What changed"]),
    "Mistakes": ("What to avoid", ["Common failure", "Cheap prevention"]),
    "CTA": ("One clear next step", ["Ask a discussion question", "Invite a concrete action"]),
}


class StoryPlanner:
    name = "story_planner"

    def plan(self, architect: ArchitectPlan, *, topic: str) -> StoryPlan:
        slides: list[SlideOutline] = []
        for idx, role in enumerate(architect.flow, start=1):
            title_seed, points = _ROLE_TEMPLATES.get(
                role,
                (f"{role} for {topic}", [f"Key point about {role.lower()}"]),
            )
            slides.append(
                SlideOutline(
                    slide_number=idx,
                    role=role,
                    title=f"{role}: {topic}" if role != "Hook" else f"{topic} — {title_seed}",
                    summary=title_seed,
                    key_points=[p if "{}" not in p else p for p in points],
                )
            )
        return StoryPlan(topic=topic, story_type=architect.story_type, slides=slides)
