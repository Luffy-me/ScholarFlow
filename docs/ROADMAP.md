# ROADMAP.md — LinkedIn Content Intelligence Engine

## Guiding Rule

Ship a strong **AI core engine** before the UI. Do **not** build the dashboard first.

Do **not** build everything at once.

Full product pipeline (target):

```text
Research → Analyze → Strategize → Write → Humanize → Critique → Improve → Export
```

Supporting layers:

- User memory + content modes
- Source evidence (`research_sources/`)
- Feedback learning (`feedback/engagement_feedback.json`)

---

## Phase 0 — Documentation & Contracts (current)

**Deliverables**

- [x] `docs/PRODUCT.md`
- [x] `docs/ARCHITECTURE.md`
- [x] `docs/DATABASE.md`
- [x] `docs/ROADMAP.md`
- [ ] Root `README.md` (after approval to implement)
- [ ] Knowledge / data contracts:
  - `knowledge/writing_rules.json`
  - `knowledge/banned_patterns.json`
  - `knowledge/user_style_profile.json`
  - `knowledge/user_memory.json`
  - `knowledge/content_modes.json`
  - `knowledge/examples/good_posts.json`
  - `knowledge/examples/bad_posts.json`
  - `feedback/engagement_feedback.json`
  - `research_sources/` (directory + schema)

**Exit criteria**

- Final architecture approved; implementation plan accepted.

---

## Phase 1 — AI Core Engine (build next)

**Do not build the web dashboard in this phase.**

### Product / technical scope

1. Ollama connection
2. Model abstraction layer
3. Writer Agent (content-mode aware)
4. Human Voice Agent
5. Critic Agent
6. Engagement Predictor Agent (`agents/engagement_predictor/score_agent.py`)
7. Save generated content
8. Content modes (`knowledge/content_modes.json`)
9. Source evidence layer (optional attach + persist)
10. Feedback learning schema (write/read real metrics; learning models later)

### Technical work breakdown

| Area | Work |
|---|---|
| Repo skeleton | `apps/api`, `agents/*`, `models/ollama`, `knowledge/*`, `research_sources/`, `feedback/`, `database/` |
| Knowledge | user memory, content modes, writing rules, banned patterns, good/bad examples |
| Evidence | `research_sources/` schema + API attach |
| Feedback | `feedback/engagement_feedback.json` + DB table + API |
| Model layer | Provider interface + Ollama adapter + FakeProvider |
| Agents (wired) | writer, humanizer, critic, engagement_predictor |
| Agents (stubs) | trend_analyzer, researcher, strategist, designer |
| API | health, AI status, modes, generate, save/list posts, memory, evidence, engagement feedback |
| DB | users, writing_profiles, posts, generated_content, feedback, research_sources, engagement_feedback |
| Tests | AI evaluation suite + provider fake, memory gate, modes, evidence, feedback API |
| Docs | README + local runbook (API-first) |

### AI evaluation tests (required)

```text
tests/
├── test_writer.py
├── test_humanizer.py
├── test_critic.py
└── test_engagement_predictor.py
```

These tests must verify:

| Assertion | Covered by |
|---|---|
| Generic AI writing is detected | `test_critic.py`, `test_engagement_predictor.py` |
| Fake personal experiences are rejected | `test_writer.py`, `test_critic.py` |
| First-person authentic writing is preferred | `test_writer.py`, `test_humanizer.py` |
| Weak hooks are identified | `test_critic.py`, `test_engagement_predictor.py` |
| Engagement scoring returns structured output | `test_engagement_predictor.py` |

Tests use `FakeProvider` and deterministic rule helpers — they must not require a live Ollama instance.

### Explicitly out of scope (Phase 1)

- Web dashboard / Next.js UI
- Automated learning/optimization from feedback (schema only)
- Live trend scraping
- Full autonomous research ingestion
- Carousel PDF/PNG export
- Cloud LLM providers (interface stub only)
- Browser extension
- Analytics product UI
- LinkedIn OAuth / publishing / scraping

### Exit criteria

- [x] AI evaluation suite exists and passes with FakeProvider.
- API (or CLI) can run: topic + mode → write → humanize → critique → engagement predict → save.
- Critic returns scores and uses good/bad examples as references.
- Engagement predictor returns required JSON (`problems`, `improvements`, dimension scores).
- Content mode changes style without inventing biography.
- Optional evidence records persist (`source`, `date`, `confidence`, `extracted_claim`).
- Engagement feedback can be recorded and read (impressions/likes/comments/reposts/saves/rating).
- Personal claims gated by `user_memory.json`.
- Tests pass with FakeProvider.

---

## Phase 1.5 — Real AI Validation

**Status:** implemented (CLI + Ollama wiring + dataset + report)

### Scope

1. OllamaProvider availability detection + `OLLAMA_MODEL` config (default `qwen3:8b`)
2. CLI: `python -m apps.api.cli.generate`
3. Dataset: `examples/test_topics.json`
4. Real generation evaluation report: `docs/VALIDATION_PHASE1_5.md`

### Exit criteria

- [x] Detect Ollama availability and fail clearly when offline/missing model
- [x] Configurable model via `OLLAMA_MODEL`
- [x] CLI prints draft, humanized text, critic scores, engagement scores
- [x] Sample topics cover AI, startups, economics, software engineering
- [x] Real generation run completed with findings + recommendations

See [VALIDATION_PHASE1_5.md](./VALIDATION_PHASE1_5.md).

---

## Phase 1.6 — Truth Layer v2 (anti-hallucination)

**Status:** implemented

### Scope

1. `agents/grounding/claim_checker.py`
2. Pipeline: Writer → Claim Checker → Humanizer → Critic → Engagement Predictor
3. Hard safety gate (`safe` / `approval_allowed`)
4. Humanizer cannot invent experiences/metrics/clients/achievements
5. Per-stage models: `WRITER_MODEL`, `CRITIC_MODEL`, `PREDICTOR_MODEL`
6. Grounding tests + before/after validation report

See [TRUTH_LAYER_V2.md](./TRUTH_LAYER_V2.md).

---

## Phase 1.7 — Verified Memory + Angle Intelligence

**Status:** implemented

### Scope

1. Verified Experience Memory System (`agents/memory_builder/`)
2. Updated `knowledge/user_memory.json` schema (v2)
3. Content Angle Agent (`agents/angle_finder/`)
4. Pipeline: Research → Angle Finder → Strategist → Writer → Claim Checker → Humanizer → Critic → Engagement Predictor
5. Tests for approved/unapproved memory reuse and multi-angle generation

See [MEMORY_AND_ANGLES.md](./MEMORY_AND_ANGLES.md).

---

## Phase 1.8 — AI Writing Quality Framework

**Status:** implemented

### Scope

1. Knowledge layer: `knowledge/ai_writing_guidelines.json`, `examples/ai_like_posts.json`, `examples/human_like_posts.json`
2. `agents/writing_quality/` analyzer (schemas, prompts, deterministic pattern detection)
3. Pipeline insert after Claim Checker, before Humanizer
4. Critic scores: truth / human authenticity / AI writing pattern risk / engagement
5. Humanizer rules tightened (clarity/flow/generic cleanup only; no invented facts/emotions/stories)
6. Tests in `tests/test_writing_quality.py`

**Not an AI detector:** evaluates low-quality AI writing patterns only; never claims authorship.

Pipeline:

```text
Research → Angle Finder → Strategist → Writer → Claim Checker →
AI Writing Quality Analyzer → Humanizer → Critic → Engagement Predictor
```

See [WRITING_QUALITY.md](./WRITING_QUALITY.md).

---

## Phase 1.9 — Insight Engine

**Status:** implemented

### Scope

1. `agents/insight_engine/` (`insight_generator.py`, `schemas.py`, `prompts.py`)
2. Trend Analysis wired before Insight Engine (`agents/trend_analyzer/`)
3. Insight shape: core_insight, why_it_matters, common_belief, new_perspective, supporting_evidence, reader_takeaway
4. Prefer counterintuitive / experiment lessons; avoid generic/motivational/obvious takes
5. Tests in `tests/test_insight_engine.py`

Pipeline:

```text
Research → Trend Analysis → Insight Engine → Angle Finder → Strategist →
Writer → Claim Checker → AI Writing Quality Analyzer → Humanizer →
Critic → Engagement Predictor
```

See [INSIGHT_ENGINE.md](./INSIGHT_ENGINE.md).

---

## Phase 1.10 — DeepSeek Reasoning Layer

**Status:** implemented

### Scope

1. `models/deepseek_provider.py` + `models/router.py`
2. DeepSeek for research / trends / insight / claim checker / critic / predictor
3. Qwen for writer / humanizer
4. Insight Engine DeepSeek output shape (`hidden_pattern`, `contrarian_view`, `originality_score`, …)
5. Debate Mode: Qwen draft → DeepSeek critique → Qwen rewrite → DeepSeek final score
6. Tests for routing, debate rejection of generic posts, insight improvement

See [DEEPSEEK_REASONING.md](./DEEPSEEK_REASONING.md).

---

## Phase 1.11 — Content Intelligence Platform (V3)

**Status:** implemented (engine-only, no UI)

### Scope

1. Research Intelligence (`agents/research/*`) + offline connectors (`connectors/*`)
2. Capability-based model orchestrator (`models/capabilities.py`, `models/orchestrator.py`)
3. Evidence graph (`knowledge/evidence/`)
4. Knowledge graph (`knowledge_graph/`)
5. Content Opportunity Engine (`agents/content_opportunity/`)
6. Unified quality score + rewrite loop (max 3, threshold 90)
7. Learning engine (recommendations only; never auto-edits prompts)
8. Docs: `INTELLIGENCE_V3.md`, `RESEARCH_PIPELINE.md`, `MODEL_ROUTING.md`, `KNOWLEDGE_GRAPH.md`

Local-first: works offline; external APIs optional and hot-registerable.

---

## Phase 2 — Simple Web Interface

### Scope

- Topic input
- Content mode select
- Generate button
- Results view (draft + critic + engagement prediction + evidence)
- Edit content
- Save drafts
- Manual engagement feedback entry
- Minimal settings (Ollama URL / default model / memory editor)

### Exit criteria

- Non-developer can generate, review scores, edit, save, and log post-performance feedback via UI.
- UI never calls LLMs directly.

---

## Phase 3 — Advanced Features

### Scope

- Trend discovery
- Source analysis (Research Agent fills `research_sources/`)
- Content Strategist in live pipeline
- Feedback-driven optimization insights (consume `engagement_feedback`)
- Carousel generation + PDF/PNG export
- Browser extension
- Analytics

### Also overlapping

- Qdrant-backed knowledge memory
- Async jobs via Redis
- Multi-provider adapters if needed
- n8n-ready automation examples

### Exit criteria

- User can research → strategize → generate → optionally export carousel.
- Feedback history informs simple optimization recommendations.
- No LinkedIn scraping unless an approved approach is documented and accepted.

---

## Final Implementation Plan (Phase 1)

### 1. Updated architecture (confirmed in docs)

Content intelligence pipeline with independent agents; local-first Ollama; user memory gate; content modes; optional source evidence; engagement predictor; feedback learning schema.

### 2. New / required files to create when coding starts

| Path | Purpose |
|---|---|
| `apps/api/` | FastAPI application |
| `agents/writer/` | Draft generation |
| `agents/humanizer/` | Authentic rewrite |
| `agents/critic/` | Quality scores |
| `agents/engagement_predictor/score_agent.py` | Pre-publish weakness scores |
| `agents/{trend_analyzer,researcher,strategist,designer}/` | Contract stubs |
| `models/` | Provider interface + Ollama (+ qwen/deepseek presets) |
| `knowledge/user_memory.json` | Personal context |
| `knowledge/content_modes.json` | Mode presets |
| `knowledge/writing_rules.json` | Writing rules |
| `knowledge/banned_patterns.json` | Banned phrases |
| `knowledge/examples/good_posts.json` | Positive references |
| `knowledge/examples/bad_posts.json` | Negative references |
| `research_sources/` | Evidence layer directory |
| `feedback/engagement_feedback.json` | Performance learning data |
| `database/migrations/` | Postgres schema |
| `README.md` | Runbook |

### 3. Dependencies (Phase 1)

- Python 3.11+
- FastAPI, Uvicorn
- Pydantic v2
- SQLAlchemy + Alembic
- httpx (Ollama)
- pytest
- PostgreSQL via Docker

**Deferred:** Next.js/Tailwind/shadcn/Framer Motion (Phase 2), Qdrant/Redis clients until needed, cloud LLM SDKs, any LinkedIn SDK/scraper.

### 4. Implementation sequence

1. Repo skeleton + tooling + Compose (Postgres)
2. Knowledge contracts (`user_memory`, `content_modes`, rules, banned, good/bad examples)
3. `research_sources/` + `feedback/engagement_feedback.json` seed schemas
4. Database migrations (Phase 1 tables including evidence + engagement_feedback)
5. Model provider interface + Ollama adapter + FakeProvider
6. Writer (mode + memory aware) → Humanizer → Critic → Engagement Predictor
7. Orchestrator + API routes (generate, save, modes, evidence, feedback)
8. Tests + README

### 5. Coding rules (during implementation)

- TypeScript strict (when Phase 2 starts)
- Python type hints
- Modular agents (no mega-prompt)
- Tests for new logic
- Update documentation
- Avoid unnecessary dependencies
- Never create fake APIs
- Never invent LinkedIn integrations
- Never scrape LinkedIn without an approved approach

---

## Risk Register

| Risk | Mitigation |
|---|---|
| Local models produce generic prose | Rules + modes + humanizer + critic + engagement predictor |
| Models invent personal stories | `user_memory.json` gate + critic claim check |
| Fake research citations | Evidence layer forbids invented sources; confidence required |
| Feedback mistaken for live LinkedIn sync | Manual entry only until approved integration |
| Engagement scores mistaken for virality | Docs + API copy: weakness detection only |
| UI built before engine quality | Phase gates: AI core → web → advanced |
| Mega-prompt collapse | Independent agent modules with schemas |

---

## Definition of Done (any phase)

- Documented behavior matches implemented behavior
- Types/schemas enforced
- Tests for new logic
- No invented external integrations
- No LinkedIn scraping without approval
- README / docs updated for architectural or user-facing changes
