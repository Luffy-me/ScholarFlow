"""Content Architect — decide story shape before any slides are written."""

from __future__ import annotations

from typing import Any

from agents.content_architect.schemas import STORY_TYPES, ArchitectPlan


_STORY_FLOWS: dict[str, list[str]] = {
    "Framework": ["Hook", "Problem", "Research", "Insight", "Framework", "Example", "Mistakes", "CTA"],
    "Case Study": ["Hook", "Context", "Challenge", "Approach", "Results", "Lessons", "Transfer", "CTA"],
    "Timeline": ["Hook", "Origin", "Milestone 1", "Milestone 2", "Milestone 3", "Inflection", "Now", "CTA"],
    "Comparison": ["Hook", "Criteria", "Option A", "Option B", "Tradeoffs", "Decision Matrix", "Recommendation", "CTA"],
    "Checklist": ["Hook", "Why it matters", "Check 1", "Check 2", "Check 3", "Check 4", "Common misses", "CTA"],
    "Roadmap": ["Hook", "Destination", "Phase 1", "Phase 2", "Phase 3", "Dependencies", "Risks", "CTA"],
    "Architecture": ["Hook", "Problem", "Constraints", "System Map", "Data Flow", "Tradeoffs", "Failure Modes", "CTA"],
    "Tutorial": ["Hook", "Prerequisites", "Step 1", "Step 2", "Step 3", "Validation", "Pitfalls", "CTA"],
    "Before / After": ["Hook", "Before", "Pain", "Intervention", "After", "Metrics", "What changed", "CTA"],
    "Problem → Solution": ["Hook", "Problem", "Why now", "Root cause", "Solution", "Proof", "Playbook", "CTA"],
    "Flywheel": ["Hook", "Loop overview", "Input", "Amplifier", "Output", "Feedback", "Failure points", "CTA"],
    "Decision Tree": ["Hook", "Question", "Branch A", "Branch B", "Criteria", "Path map", "Recommendation", "CTA"],
}


class ContentArchitect:
    """Deterministic architect — thinks before any slide generation."""

    name = "content_architect"

    def plan(
        self,
        *,
        topic: str,
        audience: str = "",
        goal: str = "",
        story_type: str | None = None,
        slides: int | None = None,
        insight: dict[str, Any] | None = None,
        research: dict[str, Any] | None = None,
    ) -> ArchitectPlan:
        chosen = self._choose_story_type(topic, story_type, insight, research)
        flow = list(_STORY_FLOWS[chosen])
        count = slides if slides and 5 <= slides <= 12 else len(flow)
        if count != len(flow):
            flow = self._resize_flow(flow, count)
        audience_final = audience or self._infer_audience(topic, research)
        goal_final = goal or self._infer_goal(chosen, topic)
        return ArchitectPlan(
            story_type=chosen,
            audience=audience_final,
            goal=goal_final,
            slides=count,
            flow=flow,
            reading_level="professional",
            objective=f"Teach a clear {chosen.lower()} on {topic}",
        )

    def _choose_story_type(
        self,
        topic: str,
        forced: str | None,
        insight: dict[str, Any] | None,
        research: dict[str, Any] | None,
    ) -> str:
        if forced and forced in STORY_TYPES:
            return forced
        t = (topic or "").lower()
        if any(k in t for k in ("vs", "compare", "comparison")):
            return "Comparison"
        if any(k in t for k in ("architecture", "system design", "pipeline")):
            return "Architecture"
        if any(k in t for k in ("roadmap", "plan", "phases")):
            return "Roadmap"
        if any(k in t for k in ("checklist", "audit")):
            return "Checklist"
        if any(k in t for k in ("timeline", "history", "evolution")):
            return "Timeline"
        if any(k in t for k in ("tutorial", "how to", "guide")):
            return "Tutorial"
        if insight and (insight.get("contrarian_view") or insight.get("hidden_pattern")):
            return "Framework"
        if research and research.get("evidence"):
            return "Problem → Solution"
        return "Framework"

    def _infer_audience(self, topic: str, research: dict[str, Any] | None) -> str:
        t = (topic or "").lower()
        if any(k in t for k in ("rag", "llm", "api", "eval", "infra")):
            return "engineers and builders"
        if any(k in t for k in ("market", "growth", "gtm")):
            return "founders and operators"
        return "professionals"

    def _infer_goal(self, story_type: str, topic: str) -> str:
        return f"Help the reader apply a practical {story_type.lower()} for {topic}"

    def _resize_flow(self, flow: list[str], count: int) -> list[str]:
        if count <= len(flow):
            # Keep hook + cta, sample middle
            if count <= 2:
                return ["Hook", "CTA"][:count]
            middle = flow[1:-1]
            keep = middle[: max(0, count - 2)]
            return [flow[0], *keep, flow[-1]][:count]
        extra = [f"Detail {i}" for i in range(1, count - len(flow) + 1)]
        return flow[:-1] + extra + [flow[-1]]
