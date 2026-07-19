# ROADMAP.md — LinkedIn Content Intelligence Engine

## Guiding Rule

Ship a strong **AI core engine** before the UI. Do **not** build the dashboard first.

Do **not** build everything at once.

Full product pipeline (target):

```text
Research → Analyze → Strategize → Write → Humanize → Critique → Improve → Export
```

---

## Phase 0 — Documentation & Contracts (current)

**Deliverables**

- [x] `docs/PRODUCT.md` (updated)
- [x] `docs/ARCHITECTURE.md` (updated)
- [x] `docs/DATABASE.md` (updated)
- [x] `docs/ROADMAP.md` (updated)
- [ ] Root `README.md` (after approval to implement)
- [ ] Knowledge contracts:
  - `writing_rules.json`
  - `banned_patterns.json`
  - `user_style_profile.json`
  - `user_memory.json`
  - `examples/good_posts.json`
  - `examples/bad_posts.json`

**Exit criteria**

- Updated architecture, MVP scope, and development order approved.

---

## Phase 1 — AI Core Engine (build next)

**Do not build the web dashboard in this phase.**

### Product / technical scope

1. Ollama connection
2. Model abstraction layer
3. Writer Agent
4. Human Voice Agent
5. Critic Agent
6. Engagement Predictor Agent (`agents/engagement_predictor/score_agent.py`)
7. Save generated content

### Technical work breakdown

| Area | Work |
|---|---|
| Repo skeleton | `apps/api`, `agents/*`, `models/ollama`, `knowledge/*`, `database/` |
| Knowledge | `user_memory.json`, writing rules, banned patterns, good/bad examples |
| Model layer | Provider interface + Ollama adapter + FakeProvider |
| Agents (wired) | writer, humanizer, critic, engagement_predictor |
| Agents (stubs) | trend_analyzer, researcher, strategist, designer |
| API | health, AI status, generate pipeline, save/list posts, memory read/update |
| DB | users, writing_profiles, posts, generated_content, feedback |
| Tests | provider fake, memory gate, critic vs examples, engagement schema, API generate/save |
| Docs | README + local runbook (API-first) |

### Explicitly out of scope (Phase 1)

- Web dashboard / Next.js UI
- Live trend scraping
- Full research ingestion
- Carousel PDF/PNG export
- Cloud LLM providers (interface stub only)
- Browser extension
- Analytics product
- LinkedIn OAuth / publishing / scraping

### Exit criteria

- API (or CLI) can run: topic → write → humanize → critique → engagement predict → save.
- Critic returns scores and uses good/bad examples as references.
- Engagement predictor returns the required JSON (`overall_score`, dimension scores, `problems`, `improvements`).
- Personal claims are gated by `user_memory.json`.
- Banned patterns are flagged.
- Tests pass with FakeProvider (Ollama optional for local smoke).

---

## Phase 2 — Simple Web Interface

### Scope

- Topic input
- Generate button
- Results view (draft + critic scores + engagement prediction)
- Edit content
- Save drafts
- Minimal settings (Ollama URL / default model / memory editor)

### Exit criteria

- Non-developer can generate, review scores, edit, and save a draft via the UI.
- UI never calls LLMs directly; all generation goes through the API.

---

## Phase 3 — Advanced Features

### Scope

- Trend discovery (Trend Research Agent + connectors)
- Source analysis (Research Agent + `research_sources`)
- Content Strategist wired into the live pipeline
- Carousel generation + PDF/PNG export
- Browser extension (optional packaging)
- Analytics (generation quality trends, score distributions)

### Also in this phase (or overlapping)

- Qdrant-backed knowledge memory
- Async jobs via Redis
- Multi-provider adapters (OpenAI / Gemini / Anthropic) if needed
- n8n-ready automation examples

### Exit criteria

- User can pick a trend, research it, strategize, generate, and optionally export a carousel.
- No LinkedIn scraping unless an approved approach is documented and accepted.

---

## Development Order (when coding is approved)

### Before writing any feature code, restate:

1. Updated architecture (this docs set)
2. New files to create
3. Dependencies
4. Implementation sequence

Then wait for confirmation if architecture changed again.

### Phase 1 implementation sequence

1. **Repo skeleton & tooling**  
   API package layout, lint/test runners, env samples, Docker Compose for Postgres (Redis optional).

2. **Knowledge contracts**  
   `user_memory.json`, `writing_rules.json`, `banned_patterns.json`, `examples/good_posts.json`, `examples/bad_posts.json`.

3. **Database migrations**  
   Phase 1 tables; stub deferred entities as needed.

4. **Model provider interface + Ollama adapter**  
   Health check, generate text/structured, FakeProvider for tests.

5. **Writer agent**  
   Format-aware prompts; inject allowed experiences from user memory; apply writing rules.

6. **Humanizer agent**  
   Rewrite pass with authenticity checklist.

7. **Critic agent**  
   Structured scores + banned-pattern detection + good/bad example references.

8. **Engagement Predictor agent**  
   `score_agent.py` with required output schema; problems + improvements.

9. **Orchestrator + API routes**  
   Sync pipeline; persist `generated_content`, `posts`, and feedback scores.

10. **Tests + README**  
    Contract tests and API-first local runbook.

### Phase 2 sequence (after Phase 1 stable)

1. Next.js app skeleton (TypeScript strict, Tailwind, shadcn/ui)
2. Generate page + results/edit/save
3. Settings + memory editor
4. UI tests / smoke checks

### Phase 3 sequence

1. Strategist + Researcher wiring
2. Trend connectors
3. Designer + export
4. Extension / analytics as separate tracks

Do **not** start Phase 3 features before the Phase 1 AI loop is stable.

---

## New Files Introduced by Architecture Updates

| Path | Purpose |
|---|---|
| `agents/engagement_predictor/` | Engagement prediction package |
| `agents/engagement_predictor/score_agent.py` | Score agent implementation |
| `knowledge/user_memory.json` | Canonical personal context |
| `knowledge/examples/good_posts.json` | Positive evaluation references |
| `knowledge/examples/bad_posts.json` | Negative evaluation references |

---

## Planned Dependencies (implementation; not installed yet)

### API / agents (Phase 1)

- Python 3.11+
- FastAPI, Uvicorn
- Pydantic v2
- SQLAlchemy + Alembic
- `httpx` (Ollama HTTP client)
- pytest
- PostgreSQL (Docker)

### Explicitly deferred

- Next.js / React / Tailwind / shadcn / Framer Motion → Phase 2
- Qdrant client → Phase 3
- Redis client → when async jobs are needed
- Cloud LLM SDKs → when adapters are approved
- LinkedIn SDKs / scrapers → never without approved approach

Avoid unnecessary dependencies.

---

## Risk Register

| Risk | Mitigation |
|---|---|
| Local models produce generic prose | Rules + humanizer + critic + engagement predictor |
| Models invent personal stories | `user_memory.json` context gate + critic claim check |
| Engagement scores mistaken for virality | Docs + UI copy: weakness detection only |
| Ollama unavailable | Clear API status errors; never fake success |
| UI built before engine quality | Phase gates: AI core → web → advanced |
| Mega-prompt collapse | Independent agent modules with schemas |
| Fake LinkedIn integrations | Explicit non-goals; no invented APIs |

---

## Definition of Done (any phase)

- Documented behavior matches implemented behavior
- Types/schemas enforced (TypeScript strict / Python type hints)
- Tests for new logic
- No invented external integrations
- No LinkedIn scraping without approval
- README / docs updated for user-facing or architectural changes
