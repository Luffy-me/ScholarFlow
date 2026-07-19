# LinkedIn Content Intelligence Engine

Local-first AI system for authentic, research-backed LinkedIn thought leadership.

This is **not** a generic AI post generator. Phase 1 ships the **AI core engine** (API + agents). No web UI yet.

## Pipeline (Phase 1)

```text
Writer → Humanizer → Critic → Engagement Predictor → Save
```

Full product target:

```text
Research → Analyze → Strategize → Write → Humanize → Critique → Improve → Export
```

## Quick start

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
pip install -e .

# optional Postgres
docker compose up -d

cp .env.example .env
# For offline/dev without Ollama:
# echo 'USE_FAKE_PROVIDER=true' >> .env

uvicorn apps.api.main:app --reload --port 8000
```

Health check: `GET http://localhost:8000/health`

Generate (requires Ollama unless `USE_FAKE_PROVIDER=true`):

```bash
curl -X POST http://localhost:8000/api/v1/generate \
  -H 'Content-Type: application/json' \
  -d '{"topic":"local AI evaluation loops","content_mode":"founder","format":"short"}'
```

## AI evaluation tests

```bash
pytest -q
```

Required suite:

| Test | Verifies |
|---|---|
| `tests/test_writer.py` | First-person authentic writing; fake experiences rejected |
| `tests/test_humanizer.py` | Prefers authentic first-person voice |
| `tests/test_critic.py` | Detects generic AI writing, fake experiences, weak hooks |
| `tests/test_engagement_predictor.py` | Structured engagement scores; weak hooks / AI patterns flagged |

Tests use `FakeProvider` and do **not** require Ollama.

## Repository layout

```text
apps/api/               FastAPI AI core
agents/                 Independent agents (writer, humanizer, critic, engagement_predictor, stubs)
models/                 Provider interface + Ollama + FakeProvider
knowledge/              Rules, user memory, content modes, good/bad examples
research_sources/       Optional evidence records
feedback/               engagement_feedback.json learning loop
database/               SQLAlchemy models + Alembic migrations
tests/                  AI evaluation suite
docs/                   PRODUCT, ARCHITECTURE, DATABASE, ROADMAP
```

## Principles

- Never invent personal experiences (only `knowledge/user_memory.json`)
- Prefer first-person, specific, human writing
- Local-first via Ollama
- No LinkedIn scraping or invented LinkedIn integrations
- No UI in Phase 1

## Docs

- [PRODUCT.md](docs/PRODUCT.md)
- [ARCHITECTURE.md](docs/ARCHITECTURE.md)
- [DATABASE.md](docs/DATABASE.md)
- [ROADMAP.md](docs/ROADMAP.md)
