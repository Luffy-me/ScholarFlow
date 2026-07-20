# Phase 1.5 — Real AI Validation Report

Generated with local Ollama (`OLLAMA_MODEL=qwen3:8b`, `OLLAMA_THINK=false`).

## Environment notes

- Ollama connected successfully at `http://127.0.0.1:11434`.
- Default model is configurable via `OLLAMA_MODEL` (default `qwen3:8b`).
- On this host, Ollama initially segfaulted when loading AMX CPU kernels under KVM. Workaround: replace Sapphire Rapids ggml CPU library with Haswell variant so inference can run.
- Full pipeline latency ≈ **3–4 minutes/topic** on CPU for Writer → Humanizer → Critic → Engagement Predictor.

## CLI

```bash
export OLLAMA_MODEL=qwen3:8b
export OLLAMA_THINK=false

python -m apps.api.cli.generate \
  --topic "Why local AI evaluation loops matter" \
  --mode engineer \
  --audience "ML engineers"

python -m apps.api.cli.validate --out examples/validation_report.json
```

Dataset: `examples/test_topics.json` (AI, startups, economics, software engineering).

## Sample generated outputs (abbreviated)

### 1) AI / engineer mode

> When I built a local RAG chatbot for a client, I thought the model size was just a checkbox... build the evaluation loop first.

- First-person: yes
- Banned generic AI phrases: none detected
- **Problem:** invents “for a client” (not in `user_memory.json`)

### 2) Startups / founder mode

> Last week, I spent a week building a fancy RAG chatbot for content drafting... building features nobody asked for.

- Strong narrative hook
- Uses allowed project “RAG chatbot” well
- **Problem:** invents “Last week” timeline + fictional user quote

### 3) Economics / researcher mode

> ... When we introduced a tiered reward system for consistent usage, retention jumped by 37%.

- Cleaner tone
- **Problem:** fabricated metric (37%) — high hallucination risk

### 4) Software engineering / engineer mode

> I built a test suite to catch phrases like "AI is transforming everything"... failed 80% of the time.

- Conceptually on-brand for the product
- **Problem:** invented failure rate; trailing hashtag cluster feels templated

## Evaluation summary (4 category samples)

| Metric | Result |
|---|---|
| First-person rate | 100% |
| Banned generic-phrase rate | 0% |
| Deterministic scanner authenticity | high |
| Real hallucination risk (manual review) | **medium–high** |
| Critic / engagement structured JSON | working |

Artifacts:

- `examples/sample_generation.json`
- `examples/validation_report.json`

## Problems found

1. **Experience hallucination beyond banned phrases**  
   Model invents clients, timelines, quotes, and percentages not present in `user_memory.json`.

2. **Deterministic hallucination detector was too narrow**  
   Caught “million-user” style claims, missed “for a client”, “retention jumped by 37%”, “failed 80%”.

3. **Critic issue formatting inconsistency**  
   Sometimes returns dict-like strings instead of clean issue strings.

4. **Humanizer can soften but still preserve invented facts**  
   Rewrites style without removing ungrounded claims.

5. **Latency**  
   Local 8B CPU pipeline is slow for interactive use (~3–4 min/topic).

6. **Platform quirk**  
   AMX CPU path segfaulted under virtualization; required library workaround.

## Recommended improvements

1. **Memory-grounded claim checker**  
   Extract personal/numeric claims and require support from `user_memory` or attached evidence; strip/rewrite otherwise.

2. **Expand banned/fake patterns**  
   Cover client claims, precise percentages, and absolute timelines unless memory contains them. (Started in `knowledge/banned_patterns.json`.)

3. **Hard critic gate before save**  
   Block `status=ready` when hallucination risk is high or evidence_quality is below threshold.

4. **Prompt tightening**  
   Explicitly forbid metrics/quotes/clients unless listed in allowed experiences; prefer “After analyzing…” fallbacks.

5. **Humanizer claim pass**  
   Add a dedicated “remove ungrounded facts” step before style rewrite.

6. **Performance**  
   Cache model; optional smaller model for critic/predictor; async stage timing metrics.

7. **Issue schema normalization**  
   Force critic/predictor issues to plain strings in post-processing.

## Verdict

Phase 1.5 validates that the **local Ollama path works end-to-end** and produces mostly first-person, non-corporate drafts.  
The main quality gap before UI is **anti-hallucination grounding**, not basic fluency.

**Do not build frontend yet** until claim-grounding is tightened.
