# LinkedIn Optimizer

## Purpose

Post-generation **optimization layer**. It never writes a post from scratch. It improves an existing draft after Writer → Claim Checker → Humanizer → Carousel Planner.

```text
Research → Reasoning → Writer → Claim Checker → Humanizer → Carousel Planner
  → LINKEDIN OPTIMIZER → Final Output
```

Independent package: `agents/linkedin_optimizer/`  
Does **not** replace Writer, Reasoning, Carousel, or Research modules.

## Rules

- Never invent facts
- Never modify verified evidence
- Always preserve author intent
- Local only — no cloud, no UI, no automation that posts

## Modules

| File | Role |
|---|---|
| `optimizer_pipeline.py` | Max 2-pass loop; final report |
| `optimizer.py` | Single improvement pass |
| `quality_analyzer.py` | Aggregate diagnostics |
| `hook_optimizer.py` | Score opening + 5 ranked alternatives |
| `structure_optimizer.py` | Rhythm / whitespace / scanning |
| `engagement_estimator.py` | Save/comment/share/follow/read-through |
| `readability_optimizer.py` | Length, jargon, formatting |
| `cta_optimizer.py` | Discussion / save / follow / none |
| `carousel_reviewer.py` | Feed fitness review (does not replace SlideReviewer) |
| `publishing_recommendations.py` | Day / window / hashtags / length |
| `post_score.py` | Multi-dimension LinkedIn score |
| `schemas.py` | Contracts |

## API

```python
from agents.linkedin_optimizer import OptimizerPipeline, OptimizerInput

pipe = OptimizerPipeline(max_passes=2)
result = await pipe.run(
    OptimizerInput(
        text=existing_draft,
        content_mode="founder",
        extra={
            "evidence_refs": ["arxiv:1"],
            "reasoning_present": True,
            "carousel_review": optional_review_dict,
        },
    )
)
report = result.as_report()
```

## Output

1. Original Draft  
2. Optimized Draft  
3. Improvement Summary  
4. LinkedIn Score (publish threshold **95**)  
5. Predicted Engagement  
6. Publishing Recommendations  

## Optimization loop

If overall score `< 95`:

1. Generate recommendations  
2. Apply safe improvements (hook alternative from existing content, whitespace, CTA)  
3. Re-score  

Maximum **2** passes.
