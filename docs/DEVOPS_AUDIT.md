# ScholarFlow — Local Dev / DevOps Audit (Phase 1)

**Date:** 2026-07-21  
**Scope:** Backend (FastAPI), frontend (Next.js), Ollama, startup workflow.

## Executive summary

| Area | Grade | Notes |
|------|-------|-------|
| Backend API | B+ | Solid routes; `/health` was minimal; startup checks improved in reliability PR |
| Ollama layer | B | Server-side only; needed `trust_env=False`, retries, sharper timeouts |
| Frontend proxy | B | `/backend/*` → `SCHOLARFLOW_API_URL`; failures often misread as “Ollama offline” |
| Pipeline | B− | Long async chain; limited per-stage logging and stage-scoped errors |
| DX / startup | C | Manual 3-terminal flow; no one-click scripts |

## 1. Backend

| Check | Finding |
|-------|---------|
| FastAPI startup | `init_db` on startup; Ollama probe logged; no directory ensure |
| Routes | `/health`, `/api/v1/ai/status`, `/api/v1/generate`, posts, memory — consistent |
| Providers | Routed via `models/router.py`; Ollama HTTP in `models/ollama/provider.py` |
| Environment | `apps/api/config.py` + `apps/api/ai_config.py`; `.env` via pydantic-settings |
| Exceptions | `apps/api/errors.py` structured handlers; pipeline stage errors added |
| Logging | Module loggers; pipeline stage logger `scholarflow.pipeline` added |
| Async | Pipeline fully async; health/status async probes |

## 2. Frontend

| Check | Finding |
|-------|---------|
| API calls | `fetch('/backend/...')` only — no direct Ollama |
| Proxy | `next.config.ts` rewrites to `127.0.0.1:8000` |
| AI status | Uses `connected` / `online`; distinguishes API vs Ollama offline |
| Loading | React Query on status; 20s refresh |

## 3. AI layer

| Check | Finding |
|-------|---------|
| Connection | `probe_ollama` + provider `health()` |
| Models | Writer/critic/predictor validated on startup (warnings only) |
| Timeouts | 5s probe; 300s generation default — connect/read split added |
| Retries | Added for transient connect/timeouts on chat |
| Malformed JSON | Empty content fallback to `thinking` field |

## 4. Development workflow

| Risk | Mitigation |
|------|------------|
| Port 8000/3000 in use | Scripts check PIDs; README troubleshooting |
| Ollama not running | `start_scholarflow.command` launches Ollama on macOS |
| Missing venv | Script creates/activates `.venv` |
| Duplicate servers | `stop_scholarflow.command` kills recorded PIDs |

## Remediation (implemented)

- `docs/DEVOPS_AUDIT.md` (this file)
- Enhanced `GET /health` with `backend`, `ollama`, `models`
- Ollama `trust_env=False`, retries, explicit timeout messages
- `apps/api/startup.py` — DB, dirs, Ollama, models
- Pipeline stage logging + `PipelineStageError`
- `scripts/start_scholarflow.command` / `stop_scholarflow.command`
- `.env.example` ports; README one-click + troubleshooting
