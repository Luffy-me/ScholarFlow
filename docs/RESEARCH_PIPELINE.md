# Research Pipeline

## Agents (`agents/research/`)

| Module | Role |
|---|---|
| `orchestrator.py` | Compose full research brief |
| `collector.py` | Pull from connector registry |
| `deduplicator.py` | URL/title dedupe |
| `source_ranker.py` | Tier + confidence + topical rank |
| `evidence_extractor.py` | Atomic claims with sources |
| `trend_detector.py` | Momentum / FAQs / pain points |
| `summarizer.py` | Brief + open questions |
| `schemas.py` / `prompts.py` | Contracts + optional LLM prompts |

## Connectors

Each connector implements:

`collect`, `normalize`, `extract_metadata`, `extract_entities`, `extract_evidence`, `calculate_confidence`, `deduplicate`

(+ `search` / `summarize` / `extract` / `confidence` compat helpers)

See `docs/RESEARCH_ACQUISITION.md` for the Phase 5 acquisition layer (source registry, RSS registry, scheduler, storage).

Register future providers without agent changes:

```python
from connectors.registry import register_connector
register_connector("tavily", TavilyConnector)
```

## Trend detector output

```json
{
  "trend": "",
  "momentum": 0,
  "confidence": 0,
  "source_count": 0,
  "supporting_sources": []
}
```

## Evidence graph

`knowledge/evidence/evidence_graph.json`

```json
{
  "claim": "",
  "supporting_sources": [],
  "contradicting_sources": [],
  "confidence": 0,
  "last_verified": "",
  "verified": false
}
```

Writer may use verified claims, or clearly attributed opinions (`attribution_required`).
