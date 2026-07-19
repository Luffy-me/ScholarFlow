# Insight Engine

## Purpose

Generate original insights **before** content creation.

## Pipeline position

```text
Research
  ↓
Trend Analysis
  ↓
Insight Engine
  ↓
Angle Finder
  ↓
Strategist
  ↓
Writer
  ↓
Claim Checker
  ↓
AI Writing Quality Analyzer
  ↓
Humanizer
  ↓
Critic
  ↓
Engagement Predictor
```

## Output

```json
{
  "core_insight": "",
  "why_it_matters": "",
  "common_belief": "",
  "new_perspective": "",
  "supporting_evidence": "",
  "reader_takeaway": ""
}
```

## Rules

Avoid:
- generic observations
- motivational statements
- obvious conclusions

Prefer:
- counterintuitive ideas
- lessons from experiments
- expert perspectives
- practical frameworks
- unique observations

## Agent

`agents/insight_engine/`

- `schemas.py`
- `prompts.py`
- `insight_generator.py` — generation + strength scoring (`is_weak` / `is_strong`)

## Tests

1. Generic AI topic → weak insight
2. Specific personal experience → stronger insight
3. Common belief vs new perspective contrast
4. Reader takeaway is actionable
