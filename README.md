# LinkedIn Content Intelligence Engine (ScholarFlow)

Local-first AI for research-backed LinkedIn content. **FastAPI** backend + **Next.js** web UI.

## Start the full stack (fresh clone)

**Terminal 1 — Ollama**

```bash
ollama serve
ollama pull qwen3:8b
ollama pull deepseek-r1:8b
```

**Terminal 2 — API**

```bash
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
pip install -e .

cp .env.example .env
python3 -m uvicorn apps.api.main:app --reload --port 8000
```

**Terminal 3 — Web UI**

```bash
cd apps/web
npm install
npm run dev
```

Open `http://localhost:3000`. The UI calls FastAPI via `/backend/*` (proxied to `http://127.0.0.1:8000`).

Health: `GET http://127.0.0.1:8000/health` → `{"status":"ok"}`  
AI status: `GET http://127.0.0.1:8000/api/v1/ai/status` (always JSON, never 500)

## Model standard

| Role | Env | Default |
|------|-----|---------|
| Writer | `WRITER_MODEL` | `qwen3:8b` |
| Humanizer | `HUMANIZER_MODEL` | `qwen3:8b` |
| Critic | `CRITIC_MODEL` | `deepseek-r1:8b` |
| Engagement predictor | `PREDICTOR_MODEL` | `deepseek-r1:8b` |

Ollama URL: `OLLAMA_BASE_URL=http://127.0.0.1:11434` (backend only — browser never talks to Ollama).

Central defaults: `apps/api/ai_config.py`.

## Offline / tests without Ollama

```bash
echo 'USE_FAKE_PROVIDER=true' >> .env
```

```bash
pytest -q
```

## Generate (API)

```bash
curl -X POST http://127.0.0.1:8000/api/v1/generate \
  -H 'Content-Type: application/json' \
  -d '{"topic":"local AI evaluation loops","content_mode":"founder","format":"short"}'
```

## Environment

| Variable | Default | Purpose |
|---|---|---|
| `OLLAMA_BASE_URL` | `http://127.0.0.1:11434` | Ollama (FastAPI only) |
| `WRITER_MODEL` | `qwen3:8b` | Writer |
| `HUMANIZER_MODEL` | `qwen3:8b` | Humanizer |
| `CRITIC_MODEL` | `deepseek-r1:8b` | Critic |
| `PREDICTOR_MODEL` | `deepseek-r1:8b` | Engagement predictor |
| `OLLAMA_THINK` | `false` | Qwen3 thinking tokens |
| `SCHOLARFLOW_API_URL` | `http://127.0.0.1:8000` | Next.js proxy target |
| `USE_FAKE_PROVIDER` | `false` | Deterministic fake LLM for tests |

See `.env.example` for the full list.

## Repository layout

```text
apps/api/               FastAPI AI core
apps/web/               Next.js UI
agents/                 Pipeline agents
models/                 Ollama providers + routing
knowledge/              Memory, modes, rules
tests/                  Test suite (FakeProvider)
docs/                   Architecture & product docs
```

## Docs

- [ARCHITECTURE.md](docs/ARCHITECTURE.md)
- [UI.md](docs/UI.md)
- [PREMIUM_UX.md](docs/PREMIUM_UX.md)
