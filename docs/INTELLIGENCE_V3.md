# Intelligence V3 — Content Intelligence Platform

## Goal

Think like a senior researcher, strategy consultant, product marketer, journalist, and technical writer **before** writing.

No UI in this phase. Local-first. Provider-agnostic. Modular.

## Pipeline

```text
Research Intelligence (connectors + evidence + trends)
  ↓
Trend Analysis
  ↓
Insight Engine (DeepSeek / reasoning capability)
  ↓
Content Opportunity scoring
  ↓
Angle Finder
  ↓
Strategist
  ↓
Writer (Qwen / writing capability)
  ↓
Debate Mode (optional)
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
  ↓
Quality Score
  ↓
Rewrite Loop (max 3) if overall < 90
```

## New modules

| Area | Path |
|---|---|
| Research agents | `agents/research/` |
| Content opportunities | `agents/content_opportunity/` |
| Quality + rewrite | `agents/quality/` |
| Connectors | `connectors/` |
| Evidence graph | `knowledge/evidence/` |
| Knowledge graph | `knowledge_graph/` |
| Learning | `learning/` |
| Capability router | `models/capabilities.py`, `models/orchestrator.py`, `models/router.py` |

## Design rules

1. **No hardcoded models in agents** — agents declare capabilities; orchestrator selects providers.
2. **Connectors are swappable** — register Firecrawl/Tavily/etc. without changing agent code.
3. **Offline works** — fixture connectors return local signals when APIs are unavailable.
4. **Writer may only use verified claims or attributed opinions** from the evidence store.
5. **Learning stores recommendations only** — never auto-modifies prompts.

## Quality score

```json
{
  "truth": 0,
  "specificity": 0,
  "clarity": 0,
  "human_voice": 0,
  "originality": 0,
  "novelty": 0,
  "reader_value": 0,
  "discussion_potential": 0,
  "engagement": 0,
  "technical_accuracy": 0,
  "overall": 0
}
```

## Related docs

- [RESEARCH_PIPELINE.md](./RESEARCH_PIPELINE.md)
- [MODEL_ROUTING.md](./MODEL_ROUTING.md)
- [KNOWLEDGE_GRAPH.md](./KNOWLEDGE_GRAPH.md)
- [DEEPSEEK_REASONING.md](./DEEPSEEK_REASONING.md)
