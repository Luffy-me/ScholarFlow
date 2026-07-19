# ARCHITECTURE.md — LinkedIn Content Intelligence Engine

## Overview

Monorepo architecture with a Next.js web app, FastAPI backend, independent AI agents, pluggable model providers, PostgreSQL for relational data, Qdrant for vector memory, and Redis for caching/queues.

```
linkedin-content-engine/
├── apps/
│   ├── web/                 # Next.js + TypeScript + Tailwind + shadcn/ui
│   └── api/                 # FastAPI + Python
├── agents/
│   ├── researcher/
│   ├── strategist/
│   ├── writer/
│   ├── humanizer/
│   ├── critic/
│   ├── designer/
│   └── trend_analyzer/
├── models/
│   ├── ollama/
│   ├── qwen/
│   └── deepseek/
├── knowledge/
│   ├── writing_rules.json
│   ├── banned_patterns.json
│   ├── user_style_profile.json
│   └── examples/
├── database/
├── docs/
└── README.md
```

---

## Design Goals

| Goal | Implication |
|---|---|
| Local-first | Ollama is the default LLM runtime; cloud providers are adapters |
| Agent isolation | Each agent has a clear contract (input schema → output schema) |
| No fake experiences | Writer/humanizer/critic share a context gate for allowed personal claims |
| Production quality | Typed APIs, migrations, tests, explicit configuration |
| Incremental delivery | MVP uses a subset of agents; later agents plug into the same orchestration bus |

---

## High-Level System Diagram

```text
┌─────────────┐     HTTPS/JSON      ┌──────────────────┐
│  apps/web   │ ──────────────────► │     apps/api     │
│  Next.js    │ ◄────────────────── │     FastAPI      │
└─────────────┘                     └────────┬─────────┘
                                             │
                    ┌────────────────────────┼────────────────────────┐
                    │                        │                        │
                    ▼                        ▼                        ▼
             ┌────────────┐           ┌────────────┐           ┌────────────┐
             │ PostgreSQL │           │   Redis    │           │   Qdrant   │
             │  (state)   │           │ cache/jobs │           │  (memory)  │
             └────────────┘           └────────────┘           └────────────┘
                                             │
                                             ▼
                                  ┌────────────────────┐
                                  │  Agent Orchestrator │
                                  └─────────┬──────────┘
            ┌───────────┬───────────┬───────┴───────┬───────────┬───────────┐
            ▼           ▼           ▼               ▼           ▼           ▼
       Researcher  Strategist   Writer         Humanizer    Critic     Designer
            │           │           │               │           │           │
            └───────────┴───────────┴───────┬───────┴───────────┴───────────┘
                                            ▼
                                   ┌────────────────┐
                                   │ Model Provider │
                                   │   Interface    │
                                   └───────┬────────┘
                     ┌─────────────────────┼─────────────────────┐
                     ▼                     ▼                     ▼
                 Ollama              OpenAI/Gemini            Anthropic
              (Qwen/DeepSeek)         (optional)             (optional)
```

---

## Frontend (`apps/web`)

### Stack

- Next.js (App Router)
- TypeScript (strict)
- Tailwind CSS
- shadcn/ui
- Framer Motion (intentional motion only; not decorative noise)

### MVP Screens

1. **Dashboard** — saved posts, recent generations, Ollama status
2. **Generate** — topic input, format select, model select, generate action
3. **Draft workspace** — original → humanized → critic scores → save
4. **Settings** — Ollama base URL, default model, writing profile basics

### Frontend responsibilities

- UI state and optimistic draft editing
- API client typed against OpenAPI / shared contracts
- No direct LLM calls from the browser (privacy + key safety)

---

## Backend (`apps/api`)

### Stack

- FastAPI
- SQLAlchemy / Alembic (or equivalent) for PostgreSQL
- Pydantic models for request/response and agent I/O
- Redis for short-lived job status and optional queueing
- Qdrant client for knowledge/memory embeddings (Phase 2+)

### API surface (MVP)

| Method | Path | Purpose |
|---|---|---|
| `GET` | `/health` | API health |
| `GET` | `/ai/status` | Ollama reachability + available models |
| `POST` | `/generate` | Run writer → humanizer → critic pipeline |
| `POST` | `/humanize` | Re-run humanizer on existing draft |
| `POST` | `/critique` | Re-run critic on existing draft |
| `GET` | `/posts` | List saved posts |
| `POST` | `/posts` | Persist generated content |
| `GET` | `/posts/{id}` | Fetch one post |
| `PATCH` | `/posts/{id}` | Update draft / status |
| `GET` | `/profile` | Writing profile |
| `PUT` | `/profile` | Update writing profile |

Exact paths may be versioned under `/api/v1`.

---

## Agent Architecture

Agents are **independent modules** with:

- Explicit input/output Pydantic schemas
- Shared access to `knowledge/*` rules
- Model calls via a provider interface (never hardcoded vendor SDKs inside agent logic)
- Deterministic post-processing where possible (banned-pattern scan)

### Agent contracts

#### 1. Trend Research Agent (`agents/trend_analyzer`)

**Purpose:** Find interesting topics before saturation.

**Sources (Phase 2+):** RSS, Hacker News, Reddit, arXiv, GitHub Trending, tech blogs.

**Output**

```json
{
  "topic": "",
  "trend_level": "",
  "why_it_matters": "",
  "possible_angles": [],
  "target_audience": ""
}
```

#### 2. Content Strategist Agent (`agents/strategist`)

**Input:** Topic + research summary

**Output**

```json
{
  "audience": "",
  "hook": "",
  "opinion": "",
  "structure": "",
  "discussion_question": ""
}
```

#### 3. LinkedIn Writer Agent (`apps` MVP core — `agents/writer`)

**Purpose:** First draft generation.

**Rules**

- First person when possible and allowed by context
- Strong opening
- Short paragraphs
- Natural writing
- Specific examples
- No AI-like phrases

**Formats:** short, long-form, carousel script, founder story, research summary, technical explanation

#### 4. Human Voice Agent (`agents/humanizer`)

**Checks**

- Sounds like a person?
- Corporate language?
- Clear perspective?
- Story present?
- Too generic?

**Improves:** sentence variation, personal tone, clarity, authenticity

#### 5. AI Writing Critic Agent (`agents/critic`)

**Scores**

```json
{
  "originality": 0,
  "human_quality": 0,
  "engagement_probability": 0,
  "evidence_quality": 0,
  "ai_pattern_score": 0
}
```

**Detects:** generic phrases, weak hooks, unsupported claims, repetition, lack of examples

Note: `ai_pattern_score` is higher when more AI-like patterns are detected (worse). Other scores are “higher is better.”

#### 6. Carousel Designer Agent (`agents/designer`)

**Output**

```json
[
  {
    "slide": 1,
    "title": "",
    "body": "",
    "visual": "",
    "design_instruction": ""
  }
]
```

**Styles:** Apple minimal, consulting, research paper, modern startup  
**Export (Phase 2+):** PDF, PNG

#### 7. Researcher Agent (`agents/researcher`)

Grounds claims with sources; feeds strategist/writer. Phase 2+.

---

## MVP Pipeline (Phase 1)

Simplified orchestration — no trend ingestion, no full researcher:

```text
Topic + format + user profile
        │
        ▼
   Writer Agent  ──► draft_v1
        │
        ▼
 Humanizer Agent ──► draft_v2
        │
        ▼
  Critic Agent   ──► scores + issues
        │
        ▼
   Persist GeneratedContent + optional Feedback seed
```

Optional Phase 1.5: insert Strategist between topic and writer if latency budget allows.

---

## Model Provider Layer (`models/`)

### Interface (conceptual)

```text
generate(messages, model, temperature, response_format?) → text | structured
health() → online models
embed(texts) → vectors   # Phase 2+
```

### Providers

| Provider | Role |
|---|---|
| `models/ollama` | Primary local runtime |
| `models/qwen` | Model presets / prompts tuned for Qwen via Ollama |
| `models/deepseek` | Model presets / prompts tuned for DeepSeek via Ollama |
| Future | OpenAI, Gemini, Anthropic adapters behind the same interface |

**Rule:** Agents depend on the interface, not on a vendor.

---

## Context Gate (Anti–Fake Experience)

Before writer/humanizer prompts are finalized, the orchestrator builds an **AllowedClaimsContext**:

- Facts from `WritingProfile` / user-provided notes
- Explicit user-supplied anecdotes for this generation
- Research snippets with source IDs (when available)

Prompt instructions forbid inventing experiences outside this set.  
Critic re-checks for experience claims not present in context.

---

## Data & Storage

| Store | Use |
|---|---|
| PostgreSQL | Users, posts, trends, feedback, carousels, profiles |
| Qdrant | Semantic memory of past posts, research chunks, style exemplars (Phase 2+) |
| Redis | Generation job status, rate limits, cache of Ollama model lists |
| Local filesystem | Carousel exports, uploaded references (cloud-compatible later) |

See [DATABASE.md](./DATABASE.md) for schemas.

---

## Configuration

Environment-driven (no secrets in repo):

- `DATABASE_URL`
- `REDIS_URL`
- `QDRANT_URL` (optional in MVP)
- `OLLAMA_BASE_URL` (default `http://localhost:11434`)
- `DEFAULT_MODEL` (e.g. `qwen2.5:14b`)
- Provider API keys only when cloud adapters are enabled

---

## Automation (n8n-ready)

API endpoints are designed to be callable from n8n without UI:

- Trigger generation with topic payload
- Poll job status (when async)
- Fetch saved post JSON

No n8n workflows ship in MVP; contracts stay automation-friendly.

---

## Security & Privacy

- Local-first: default path keeps prompts/content on the user’s machine via Ollama
- Browser never holds cloud provider keys
- User style profiles treated as sensitive personal data
- No silent LinkedIn publishing

---

## Testing Strategy

| Layer | Focus |
|---|---|
| Unit | Banned-pattern detector, score aggregation, schema validation |
| Agent contract | Fixture prompts → structured outputs parse correctly |
| API | Generate/save/list with mocked LLM provider |
| E2E (later) | Dashboard → generate → critique → save |

Use a **FakeProvider** in tests — never invent live external APIs.

---

## Technical Decisions (Summary)

1. **Monorepo** — shared contracts and one PR surface for web + API + agents.
2. **FastAPI + Next.js** — typed JSON APIs, clear separation of UI and AI orchestration.
3. **Agent modules over one mega-prompt** — measurable quality steps and replaceable stages.
4. **Ollama-first provider** — local default; cloud is optional adapters.
5. **PostgreSQL for MVP state** — Qdrant deferred until memory/search is needed.
6. **Knowledge JSON as product rules** — writing constraints are versioned assets, not buried in code.
7. **Redis optional-but-planned** — MVP can run sync generation; Redis enables async jobs without redesign.
