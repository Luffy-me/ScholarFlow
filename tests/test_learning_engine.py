"""Learning engine tests — recommendations only, no prompt mutation."""

from __future__ import annotations

from learning import LearningEngine


def test_learning_extracts_recommendations_only(tmp_path) -> None:
    engine = LearningEngine(tmp_path / "recs.json")
    text = (
        "I tested local models and the evaluation loop was the bottleneck.\n\n"
        "What would you measure first?"
    )
    result = engine.record_engagement(
        post_id="p1",
        text=text,
        likes=12,
        comments=4,
        shares=2,
        saves=3,
        impressions=1000,
    )
    assert result["event"]["likes"] == 12
    recs = engine.recommendations()
    assert recs
    assert any("hook" in r.lower() or "cta" in r.lower() or "length" in r.lower() or "structure" in r.lower() for r in recs)
    # Engine must not expose prompt-rewriting actions.
    blob = " ".join(recs).lower()
    assert "modify prompt" not in blob
    assert "overwrite system prompt" not in blob


def test_learning_low_engagement_collect_more_samples(tmp_path) -> None:
    engine = LearningEngine(tmp_path / "recs2.json")
    engine.record_engagement(post_id="p2", text="Short post", likes=0, comments=0)
    assert any("collect more" in r.lower() for r in engine.recommendations())
