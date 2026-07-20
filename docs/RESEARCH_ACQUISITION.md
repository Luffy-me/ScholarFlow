# Research Acquisition Layer (Phase 5)

Local-first, modular data acquisition. No UI. Network optional (`ACQUISITION_OFFLINE=1` forces fixtures).

## Layout

| Path | Role |
|---|---|
| `connectors/` | Real + offline connectors implementing the acquisition contract |
| `acquisition/source_registry.py` | Authority, freshness, update frequency, category, trust, parser |
| `acquisition/rss_registry.py` | Curated feeds by topic domain |
| `acquisition/storage.py` | Research cache, knowledge storage, cleanup, Drive mirror backup |
| `acquisition/scheduler.py` | Automatic download → evidence → knowledge graph → raw cleanup |

## Connector contract

Every connector implements:

- `collect()`
- `normalize()`
- `extract_metadata()`
- `extract_entities()`
- `extract_evidence()`
- `calculate_confidence()`
- `deduplicate()`

Live connectors use `RealConnector` (HTTP then offline fallback).

## Shipped connectors

RSS, GitHub Trending, GitHub Releases, arXiv, Papers With Code, Semantic Scholar, OpenAlex, Crossref, Hacker News, Reddit, Product Hunt, HuggingFace Models, HuggingFace Papers, OpenAI / Anthropic / DeepMind / Cloudflare / Stripe / Vercel / Linear / Netflix / Uber / Shopify / Stack Overflow blogs, Dev.to, Medium (RSS only), Hashnode — plus compat aliases (`github`, `huggingface`, etc.).

Hot-register without core changes:

```python
from connectors.registry import register_connector
from acquisition import SourceRegistry
from acquisition.source_registry import SourceSpec

register_connector("tavily", TavilyConnector)
SourceRegistry().register(
    SourceSpec(
        name="tavily",
        authority_score=0.8,
        freshness_weight=0.9,
        update_frequency="hourly",
        category="ai",
        trust_level="medium",
        parser="tavily",
        tier=2,
    ),
    factory=TavilyConnector,
)
```

## RSS Registry categories

AI · Machine Learning · Economics · Finance · Business · Programming · Open Source · Cybersecurity · Cloud · Startups

## Intelligence Scheduler

```python
from acquisition import IntelligenceScheduler

sched = IntelligenceScheduler(topics=["RAG evaluation"], interval_seconds=3600)
result = sched.run_once_sync()   # one cycle
# sched.start()                  # background loop
# sched.stop()
```

Each cycle:

1. Collects from registered sources (cache-aware)
2. Extracts evidence into the evidence store
3. Updates the knowledge graph
4. Deletes raw downloads older than 24 hours

## Storage Manager

- `data/acquisition/research_cache/` — per-source query cache
- `data/acquisition/knowledge/` — briefs + graphs used by the scheduler
- `data/acquisition/raw_downloads/` — temporary raw payloads (24h TTL)
- Google Drive: set `ACQUISITION_GDRIVE_DIR` to a Drive sync folder; `backup_to_google_drive()` copies a zip there (no Google API dependency)

## Environment

| Variable | Meaning |
|---|---|
| `ACQUISITION_OFFLINE=1` | Force offline fixtures |
| `ACQUISITION_HTTP_TIMEOUT` | HTTP timeout seconds (default 8) |
| `ACQUISITION_DATA_DIR` | Override storage root |
| `ACQUISITION_GDRIVE_DIR` | Local Drive mirror for backups |
