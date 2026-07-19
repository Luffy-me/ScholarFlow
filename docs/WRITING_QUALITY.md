# AI Writing Quality Framework

## Purpose

Detect patterns commonly associated with low-quality AI writing and improve authenticity.

**Not an AI detector.** The system must never claim: “This was written by AI.”

It evaluates: “Does this content contain patterns commonly associated with low-quality AI writing?”

## Pipeline position

```text
Research
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

## Knowledge

- `knowledge/ai_writing_guidelines.json` — detection categories + preferred human patterns
- `knowledge/examples/ai_like_posts.json`
- `knowledge/examples/human_like_posts.json`

## Agent

`agents/writing_quality/`

- `schemas.py` — input/output contracts
- `prompts.py` — optional LLM enrichment (improvements only)
- `analyzer.py` — deterministic pattern detection + scoring

## Critic scores (framework)

```json
{
  "truth_score": 0,
  "human_quality_score": 0,
  "ai_pattern_risk": 0,
  "engagement_score": 0
}
```

## Humanizer rules

May: clarity, sentence flow, remove generic phrases, natural tone.  
Must not: create experiences, achievements, metrics, new emotions, or invented stories.

## Before / after examples

### Generic opening (high pattern risk)

**Before:**
> In today's rapidly evolving world, AI is revolutionizing industries.

**After direction:**
> I tested Qwen locally on my MacBook and noticed that workflow design mattered more than model size.

### Vague claim

**Before:**
> Studies show AI will replace all developers.

**Detected:** `vague_claims`, `unnatural_certainty`  
**After direction:** replace with a verified observation or hedged opinion grounded in memory.

### Verified vs unverified experience

**Allowed (if verified):**
> I built ScholarFlow using RAG architecture.

**Rejected unless verified:**
> I helped 10000 users increase productivity.
