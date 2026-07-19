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

`collect`, `search`, `summarize`, `extract`, `normalize`, `confidence`

Shipped (offline-capable fixtures):

- Tier 1: `official_docs`, `arxiv`, `paperswithcode`, `github`, `huggingface`, `awesome_lists`
- Tier 2: `hackernews`, `lobsters`, `reddit`, `devto`, `medium`, `producthunt`, `rss`, `google_news`, `stackoverflow`
- Tier 3: `youtube`
- Placeholders: `linkedin`, `x`, `news_api`

Register future providers without agent changes:

```python
from connectors.registry import register_connector
register_connector("tavily", TavilyConnector)
```

Supported future resources (architecture-ready): Firecrawl, Jina, Tavily, Exa, Perplexity, OpenAlex, Semantic Scholar, Crossref, GitHub Search API, Reddit API, NewsAPI, GDELT, RSS.

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
