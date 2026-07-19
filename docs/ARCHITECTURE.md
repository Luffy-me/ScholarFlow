# ARCHITECTURE.md — LinkedIn Content Intelligence Engine

## Overview

Monorepo architecture with a Next.js web app, FastAPI backend, independent AI agents, pluggable model providers, PostgreSQL for relational data, Qdrant for vector memory, and Redis for caching/queues.

This is a **content intelligence system**, not a single-prompt text generator.

Full product pipeline:

```text
Trend Research → Research → Strategize → Write → Humanize → Critique → Engagement Predict → Final Content → Export
```

```
linkedin-content-engine/
├── apps/
│   ├── web/                 # Next.js + TypeScript + Tailwind + shadcn/ui (Phase 2)
│   └── api/                 # FastAPI + Python (Phase 1+)
├── agents/
│   ├── trend_analyzer/
│   ├── researcher/
│   ├── strategist/
│   ├── writer/
│   ├── humanizer/
│   ├── critic/
│   ├── engagement_predictor/
│   │    └── score_agent.py
│   └── designer/
├── models/
│   ├── ollama/
│   ├── qwen/
│   └── deepseek/
├── knowledge/
│   ├── writing_rules.json
│   ├── banned_patterns.json
│   ├── user_style_profile.json
│   ├── user_memory.json          # canonical personal context
│   └── examples/
│       ├── good_posts.json
│       └── bad_posts.json
├── database/
├── docs/
└── README.md
```

---

## Design Goals

| Goal | Implication |
|---|---|
| Local-first | Ollama is the default LLM runtime; cloud providers are adapters |
| Agent isolation | Each agent has clear responsibility + input/output schemas |
| No mega-prompts | Pipeline stages are independent modules |
| No fake experiences | All personal claims gated by `user_memory.json` |
| AI core before UI | Phase 1 ships engine + API; Phase 2 adds simple web UI |
| Production quality | Typed APIs, migrations, tests, explicit configuration |

---

## High-Level System Diagram

```text
┌─────────────┐     HTTPS/JSON      ┌──────────────────┐
│  apps/web   │ ──────────────────► │     apps/api     │
│  (Phase 2)  │ ◄────────────────── │     FastAPI      │
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
       ┌──────────┬──────────┬───────┬──────┴───┬──────────┬──────────┬──────────┐
       ▼          ▼          ▼       ▼          ▼          ▼          ▼          ▼
   Trend     Research  Strategist Writer  Humanizer   Critic  Engagement Designer
  Analyzer                                       Predictor
       │          │          │       │          │          │          │          │
       └──────────┴──────────┴───────┴──────┬───┴──────────┴──────────┴──────────┘
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

## Full Agent Pipeline

Each agent is an **independent module** with:

- Clear responsibility
- Input schema
- Output schema
- No reliance on one large shared prompt

```text
Trend Research Agent
        ↓
Research Agent
        ↓
Content Strategist Agent
        ↓
LinkedIn Writer Agent
        ↓
Human Voice Agent
        ↓
AI Critic Agent
        ↓
Engagement Predictor Agent
        ↓
Final Content (+ optional Improve / Export)
```

---

## Agent Contracts

### 1. Trend Research Agent (`agents/trend_analyzer`)

**Purpose:** Find interesting topics before saturation.

**Sources (Phase 3):** RSS, Hacker News, Reddit, arXiv, GitHub Trending, tech blogs.

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

### 2. Research Agent (`agents/researcher`)

**Purpose:** Gather trusted source summaries and evidence for a topic.

**Output (conceptual)**

```json
{
  "topic": "",
  "key_findings": [],
  "sources": [
    {
      "title": "",
      "url": "",
      "source_type": "article",
      "summary": ""
    }
  ],
  "open_questions": []
}
```

### 3. Content Strategist Agent (`agents/strategist`)

**Input:** Topic + research

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

### 4. LinkedIn Writer Agent (`agents/writer`)

**Purpose:** Generate the first draft.

**Rules**

- First person when possible and allowed by `user_memory.json`
- Strong opening
- Short paragraphs
- Natural writing
- Specific examples
- No AI-like phrases

**Formats:** short, long-form, carousel script, founder story, research summary, technical explanation

### 5. Human Voice Agent (`agents/humanizer`)

**Checks**

- Sounds like a person?
- Unnecessary corporate language?
- Clear perspective?
- Story present?
- Too generic?

**Improves:** sentence variation, personal tone, clarity, authenticity

### 6. AI Writing Critic Agent (`agents/critic`)

**Purpose:** Quality control against rules + evaluation dataset.

**References:** `knowledge/examples/good_posts.json`, `knowledge/examples/bad_posts.json`

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

**Detects:** generic phrases, weak hooks, unsupported claims, repetition, lack of examples, resemblance to bad exemplars

Note: `ai_pattern_score` is higher when more AI-like patterns are detected (worse). Other scores are “higher is better.”

### 7. Engagement Predictor Agent (`agents/engagement_predictor`)

**Module:** `agents/engagement_predictor/score_agent.py`

**Purpose:** Predict potential **quality** of a LinkedIn post before publishing — identify weak content, not viral success.

**Analyzes**

- Hook strength
- Originality
- Specificity
- Story quality
- Discussion potential
- Evidence quality
- Emotional connection
- AI-writing risk

**Output**

```json
{
  "overall_score": 0,
  "hook_score": 0,
  "originality_score": 0,
  "specificity_score": 0,
  "discussion_score": 0,
  "ai_pattern_score": 0,
  "problems": [],
  "improvements": []
}
```

Score semantics:

- `overall_score`, `hook_score`, `originality_score`, `specificity_score`, `discussion_score`: higher is better (0–100)
- `ai_pattern_score`: higher means more AI-like risk (worse)
- `problems` / `improvements`: actionable strings for the improve loop

### 8. Carousel Designer Agent (`agents/designer`)

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
**Export (Phase 3):** PDF, PNG

---

## Phase 1 Pipeline (AI Core Engine)

Phase 1 does **not** build the dashboard first. It ships the core engine behind the API (CLI-friendly).

```text
Topic + format + user_memory.json
        │
        ▼
   Writer Agent          ──► draft_v1
        │
        ▼
 Humanizer Agent         ──► draft_v2
        │
        ▼
  Critic Agent           ──► quality scores + issues
        │                    (uses good/bad post examples)
        ▼
 Engagement Predictor    ──► pre-publish weakness report
        │
        ▼
 Persist GeneratedContent + Feedback scores
```

Trend / Research / Strategist / Designer remain **contract stubs** until Phase 3 (or earlier if pulled forward deliberately).

Optional improve loop (still Phase 1-compatible): if engagement `overall_score` is below a threshold, re-run humanizer (or a light rewrite) with `problems` + `improvements` injected — without collapsing agents into one prompt.

---

## User Memory Layer

### Canonical file: `knowledge/user_memory.json`

Purpose: let agents understand the user’s **real** background, projects, expertise, and writing style.

**Stores**

- Professional background
- Skills
- Projects
- Personal experiences
- Preferred topics
- Writing tone
- Vocabulary preference
- Content preferences

**Example shape**

```json
{
  "background": [
    "AI projects",
    "Computer Science",
    "Economics"
  ],
  "skills": [],
  "projects": [
    "RAG chatbot",
    "LinkedIn Content Intelligence Engine"
  ],
  "experiences": [],
  "preferred_topics": [],
  "style": {
    "first_person": true,
    "tone": "technical founder",
    "sentence_style": "short and clear"
  },
  "vocabulary_preferences": [],
  "content_preferences": []
}
```

### Context gate

Before writer/humanizer prompts are finalized, the orchestrator builds **AllowedClaimsContext** from:

1. `knowledge/user_memory.json` (primary)
2. Optional DB `writing_profiles` snapshot (synced from memory)
3. Explicit session notes (must be persisted into memory before treated as lived experience for future runs)

Prompt instructions forbid inventing experiences outside this set.  
Critic and Engagement Predictor re-check for experience claims not present in memory.

---

## Content Evaluation Dataset

Located under `knowledge/examples/`:

| File | Purpose |
|---|---|
| `good_posts.json` | Strong hooks, personal stories, clear opinions, specific examples, useful insights |
| `bad_posts.json` | Generic AI writing, corporate language, empty statements, fake expertise, motivational filler |

The **Critic Agent** loads these as few-shot / contrastive references.  
The **Engagement Predictor** may also use them as calibration hints for hook/specificity/discussion signals.

---

## Frontend (`apps/web`) — Phase 2

### Stack

- Next.js (App Router)
- TypeScript (strict)
- Tailwind CSS
- shadcn/ui
- Framer Motion (intentional motion only)

### Phase 2 screens (simple)

1. Topic input
2. Generate button
3. Results view (draft + critic + engagement scores)
4. Edit content
5. Save drafts
6. Minimal settings (Ollama URL / model)

### Frontend responsibilities

- UI state and draft editing
- Typed API client
- No direct LLM calls from the browser

---

## Backend (`apps/api`) — Phase 1+

### Stack

- FastAPI
- Python type hints everywhere
- SQLAlchemy / Alembic for PostgreSQL
- Pydantic models for request/response and agent I/O
- Redis for short-lived job status (optional in Phase 1)
- Qdrant client for embeddings (Phase 3+)

### API surface (Phase 1)

| Method | Path | Purpose |
|---|---|---|
| `GET` | `/health` | API health |
| `GET` | `/ai/status` | Ollama reachability + available models |
| `POST` | `/generate` | Writer → humanizer → critic → engagement predictor |
| `POST` | `/humanize` | Re-run humanizer |
| `POST` | `/critique` | Re-run critic |
| `POST` | `/predict-engagement` | Re-run engagement predictor |
| `GET` | `/posts` | List saved posts |
| `POST` | `/posts` | Persist generated content |
| `GET` | `/posts/{id}` | Fetch one post |
| `PATCH` | `/posts/{id}` | Update draft / status |
| `GET` | `/memory` | Read user memory (file/DB projection) |
| `PUT` | `/memory` | Update user memory |

Exact paths may be versioned under `/api/v1`.

---

## Model Provider Layer (`models/`)

### Interface (conceptual)

```text
generate(messages, model, temperature, response_format?) → text | structured
health() → online models
embed(texts) → vectors   # later phases
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

## Data & Storage

| Store | Use |
|---|---|
| PostgreSQL | Users, posts, trends, feedback, carousels, profiles, engagement scores |
| Filesystem knowledge | `user_memory.json`, rules, good/bad examples (source of truth for local-first) |
| Qdrant | Semantic memory of past posts, research chunks (Phase 3+) |
| Redis | Generation job status, rate limits, model list cache |
| Local filesystem | Carousel exports, uploaded references |

See [DATABASE.md](./DATABASE.md) for schemas.

---

## Configuration

Environment-driven (no secrets in repo):

- `DATABASE_URL`
- `REDIS_URL` (optional in Phase 1)
- `QDRANT_URL` (optional until Phase 3)
- `OLLAMA_BASE_URL` (default `http://localhost:11434`)
- `DEFAULT_MODEL` (e.g. `qwen2.5:14b`)
- `USER_MEMORY_PATH` (default `knowledge/user_memory.json`)
- Provider API keys only when cloud adapters are enabled

---

## Automation (n8n-ready)

API endpoints remain callable without UI:

- Trigger generation with topic payload
- Poll job status (when async)
- Fetch saved post JSON + scores

No n8n workflows ship in Phase 1.

---

## Security & Privacy

- Local-first: default path keeps prompts/content on the user’s machine via Ollama
- Browser never holds cloud provider keys
- `user_memory.json` treated as sensitive personal data
- No silent LinkedIn publishing
- No LinkedIn scraping without an approved approach
- No invented LinkedIn integrations or fake APIs

---

## Testing Strategy

| Layer | Focus |
|---|---|
| Unit | Banned-pattern detector, score schema validation, memory gate |
| Agent contract | Writer/humanizer/critic/predictor structured outputs |
| Evaluation fixtures | Critic distinguishes good vs bad example posts |
| API | Generate/save with FakeProvider |
| UI (Phase 2) | Topic → generate → edit → save |

Use a **FakeProvider** in tests — never invent live external APIs.

---

## Development Rules (Implementation)

When coding is approved:

- Use TypeScript strictly (web)
- Use Python type hints (API/agents)
- Write modular code (one agent = one module)
- Create tests
- Update documentation
- Avoid unnecessary dependencies
- Never create fake APIs
- Never invent LinkedIn integrations
- Never scrape LinkedIn without an approved approach

---

## Technical Decisions (Summary)

1. **Monorepo** — shared contracts across web, API, agents, knowledge.
2. **Independent agents** — Research → … → Engagement Predict; no mega-prompt.
3. **Ollama-first provider** — local default; cloud optional later.
4. **AI core before UI** — Phase 1 engine/API; Phase 2 simple web; Phase 3 advanced.
5. **`user_memory.json` as personal-claim source of truth** — never invent experiences.
6. **Good/bad post dataset** — critic calibration and regression tests.
7. **Engagement predictor ≠ virality oracle** — pre-publish weakness detection only.
8. **PostgreSQL for persisted generations** — filesystem knowledge for local rules/memory.
