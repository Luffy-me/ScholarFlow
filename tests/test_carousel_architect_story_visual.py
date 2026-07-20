"""Carousel architect / story / visual planner tests."""

from __future__ import annotations

from agents.content_architect import STORY_TYPES, ContentArchitect
from agents.story_planner import StoryPlanner
from agents.visual_planner import VisualPlanner


def test_architect_returns_required_shape() -> None:
    plan = ContentArchitect().plan(topic="local LLM evaluation loops", audience="engineers")
    payload = plan.as_dict()
    assert payload["story_type"] in STORY_TYPES
    assert payload["audience"]
    assert payload["goal"]
    assert payload["slides"] >= 5
    assert isinstance(payload["flow"], list) and payload["flow"]


def test_architect_story_type_detection() -> None:
    a = ContentArchitect()
    assert a.plan(topic="RAG vs fine-tuning comparison").story_type == "Comparison"
    assert a.plan(topic="system architecture for agents").story_type == "Architecture"
    assert a.plan(topic="product roadmap 2026").story_type == "Roadmap"
    assert a.plan(topic="security checklist").story_type == "Checklist"
    assert a.plan(topic="history timeline of transformers").story_type == "Timeline"
    assert a.plan(topic="how to build an eval harness tutorial").story_type == "Tutorial"


def test_architect_respects_forced_story_type_and_slide_count() -> None:
    plan = ContentArchitect().plan(topic="AI", story_type="Flywheel", slides=6)
    assert plan.story_type == "Flywheel"
    assert plan.slides == 6
    assert len(plan.flow) == 6
    assert plan.flow[0] == "Hook"
    assert plan.flow[-1] == "CTA"


def test_story_planner_slide_roles() -> None:
    architect = ContentArchitect().plan(topic="evaluation loops", story_type="Framework")
    story = StoryPlanner().plan(architect, topic="evaluation loops")
    assert len(story.slides) == architect.slides
    assert story.slides[0].role == "Hook"
    assert story.slides[-1].role == "CTA"
    assert all(s.title and s.summary for s in story.slides)


def test_visual_planner_chooses_visual_not_text() -> None:
    architect = ContentArchitect().plan(topic="agent pipelines", story_type="Architecture")
    story = StoryPlanner().plan(architect, topic="agent pipelines")
    visuals = VisualPlanner().plan(story)
    assert len(visuals) == len(story.slides)
    for item in visuals:
        payload = item.visual.as_dict()
        assert payload["type"]
        assert payload["reason"]
        assert payload["priority"] in {"primary", "secondary", "supporting"}
