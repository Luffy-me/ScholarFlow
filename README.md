# LinkedIn Content Intelligence Engine (ScholarFlow)

Local-first AI for research-backed LinkedIn content. **FastAPI** backend + **Next.js** web UI.

## Start ScholarFlow with one click

**macOS:** double-click:

```text
scripts/start_scholarflow.command
```

Or from a terminal:

```bash
./scripts/start_scholarflow.command
```

This script will:

1. Detect the project root automatically  
2. Check that Ollama is installed  
3. Start Ollama if it is not already running  
4. Verify required models (`qwen3:8b`, `deepseek-r1:8b`) and **pull** any that are missing  
5. Start FastAPI on port **8000** (skips if already listening)  
6. Start Next.js on port **3000** (skips if already listening)  
7. Open `http://localhost:3000`  
8. Write logs under `.scholarflow/logs/`

**Stop** (FastAPI + Next.js only — Ollama stays up):

```bash
./scripts/stop_scholarflow.command
```

**Restart** (stop then start):

```bash
./scripts/restart_scholarflow.command
```

Logs and PID files: `.scholarflow/`

## Manual start (fresh clone)

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

Health: `GET http://127.0.0.1:8000/health` → `status`, `backend`, `ollama`, `models`  
AI status: `GET http://127.0.0.1:8000/api/v1/ai/status` (always JSON, never 500)

## Troubleshooting

| Symptom | Fix |
|---------|-----|
| **Ollama not detected** | Run `ollama serve`; pull `qwen3:8b` and `deepseek-r1:8b` |
| **Port already in use** | Run `scripts/stop_scholarflow.command` or free ports `8000` / `3000` |
| **Model missing** | `ollama pull <model>` — check Settings or `/api/v1/ai/status` `missing_models` |
| **Database error** | Delete `linkedin_content.db` or fix `DATABASE_URL` in `.env` |
| **UI shows API offline** | Start uvicorn; confirm `SCHOLARFLOW_API_URL=http://127.0.0.1:8000` |

See [DEVOPS_AUDIT.md](docs/DEVOPS_AUDIT.md) for the full audit.

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
