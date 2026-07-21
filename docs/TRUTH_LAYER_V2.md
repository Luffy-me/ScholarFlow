# Truth Layer v2 — Grounding Report

## Pipeline

```text
Writer → Claim Checker → Humanizer → Critic → Engagement Predictor
```

Hard safety gate:
- unsupported personal claims ⇒ `safe=false`, `approval_allowed=false`, status `unsafe`
- API blocks `ready`/`reviewed` approval while ungrounded claims remain

## Models

| Stage | Env var | Default |
|---|---|---|
| Writer | `WRITER_MODEL` | `qwen3:8b` |
| Critic | `CRITIC_MODEL` | `deepseek-r1:8b` |
| Predictor | `PREDICTOR_MODEL` | `deepseek-r1:8b` |

## Before / after (same failure modes)

### Fake client

**Before (Phase 1.5 shipped text):**
> When I built a local RAG chatbot **for a client**, I thought the model size was just a checkbox...

**Claim checker:** `rejected_claims=[{claim_type: client}]`  
**After Truth Layer v2:** client sentence removed / replaced with grounded scaffold  
**Approval:** not allowed until clean

### Fake metric

**Before:**
> ... **retention jumped by 37%**.

**Claim checker:** `rejected_claims=[{claim_type: metric}]`  
**After:** metric removed  
**Approval:** blocked if residual remains

### Fake time reference (even with valid project)

**Before-style draft:**
> **Last week**, I tested two RAG chatbots...

**Claim checker:** `rejected_claims=[{claim_type: time_reference}]`  
**After:** time-marked sentence stripped even though “RAG chatbot” is in memory

### Valid project memory

**Input:**
> I built a RAG chatbot and kept making the same mistake...

**Claim checker:** approved  
**Approval:** allowed

## Validation rerun (`examples/validation_report_v2.json`)

| Metric | Phase 1.5 | Truth Layer v2 |
|---|---|---|
| Fake clients/metrics in final posts | Yes | **No** |
| Grounding safe rate | n/a | **100%** |
| Approval allowed rate | implicit yes | **100%** (after sanitize) |
| Generic AI phrase rate | 0% | 0% |
| First-person density | High | Lower* |

\*Expected: aggressive claim removal can leave sparse but truthful drafts. Safer sparse truth > fluent fiction.

## Sample after outputs (final text)

### AI
Grounded local/cloud comparison without inventing a client relationship.

### Startups
Keeps product lesson framing; strips unsupported “last week” / invented quotes when present in raw writer output.

### Economics
No fabricated retention percentage.

### Software engineering
CI metaphor retained without invented failure-rate statistics.

## Tests

`tests/test_grounding.py`
- fake client claim rejected
- fake metric rejected
- valid project accepted
- personal memory used correctly
- sanitize removes client/time
- fake quote rejected
- time reference rejected even with valid project

Unit suite: **19 passed**.
