# Insight Engine

## Purpose

Generate original insights **before** content creation using **DeepSeek reasoning**.

## Pipeline position

```text
Research (DeepSeek)
  ↓
Trend Analysis (DeepSeek)
  ↓
Insight Engine (DeepSeek)
  ↓
Angle Finder
  ↓
Strategist
  ↓
Writer (Qwen)
  ↓
Debate Mode
  ↓
…
```

## Output

```json
{
  "hidden_pattern": "",
  "common_belief": "",
  "contrarian_view": "",
  "why_it_matters": "",
  "supporting_reasoning": "",
  "reader_takeaway": "",
  "originality_score": 0
}
```

## Rules

Avoid:
- generic observations
- motivational statements
- obvious conclusions

Prefer:
- hidden patterns
- counterintuitive / contrarian views
- lessons from experiments
- practical frameworks
- unique observations

## Agent

`agents/insight_engine/`

- `schemas.py`
- `prompts.py`
- `insight_generator.py`

Routed via `models/router.py` to the DeepSeek family.
