# ARCHITECTURE.md — LinkedIn Content Intelligence Engine

## Overview

Monorepo architecture with a Next.js web app, FastAPI backend, independent AI agents, pluggable model providers, PostgreSQL for relational data, Qdrant for vector memory, and Redis for caching/queues.

This is a **content intelligence system**, not a single-prompt text generator.

Full product pipeline:

```text
Research → Angle Finder → Strategist → Writer → Claim Checker →
AI Writing Quality Analyzer → Humanizer → Critic → Engagement Predictor → Export
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
│   ├── angle_finder/
│   ├── writer/
│   ├── grounding/           # Truth Layer claim checker
│   ├── writing_quality/     # AI Writing Quality Framework
│   ├── humanizer/
│   ├── critic/
│   ├── engagement_predictor/
│   │    └── score_agent.py
│   ├── memory_builder/
│   └── designer/
├── models/
│   ├── ollama/
│   ├── qwen/
│   └── deepseek/
├── knowledge/
│   ├── writing_rules.json
│   ├── banned_patterns.json
│   ├── ai_writing_guidelines.json
│   ├── user_style_profile.json
│   ├── user_memory.json          # canonical personal context
│   ├── content_modes.json        # founder / researcher / engineer / career_journey
│   └── examples/
│       ├── good_posts.json
│       ├── bad_posts.json
│       ├── ai_like_posts.json
│       └── human_like_posts.json
├── research_sources/             # source evidence layer (files)
├── feedback/
│   └── engagement_feedback.json  # real performance learning loop
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
| Evidence-aware | Insights may attach source/date/confidence/claim |
| Mode-aware writing | Content modes shape voice without inventing biography |
| Learn from reality | Manual engagement feedback enables future optimization |
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
- Apply selected **content mode** from `knowledge/content_modes.json`
- Strong opening
- Short paragraphs
- Natural writing
- Specific examples
- No AI-like phrases
- Prefer attaching optional source evidence when research claims are used

**Formats:** short, long-form, carousel script, founder story, research summary, technical explanation

**Modes:** `founder`, `researcher`, `engineer`, `career_journey`

### 5. AI Writing Quality Analyzer (`agents/writing_quality`)

**Purpose:** Detect patterns commonly associated with low-quality AI writing and suggest authenticity improvements.

**This is not an AI detector.** The system must never claim “this was written by AI.”

**Knowledge:** `knowledge/ai_writing_guidelines.json`, `knowledge/examples/ai_like_posts.json`, `knowledge/examples/human_like_posts.json`

**Input**

```json
{
  "content": "",
  "content_mode": "",
  "verified_memory": []
}
```

**Output**

```json
{
  "human_quality_score": 0,
  "ai_pattern_risk": 0,
  "specificity_score": 0,
  "originality_score": 0,
  "detected_patterns": [
    {
      "category": "",
      "severity": "",
      "example": "",
      "explanation": ""
    }
  ],
  "improvements": []
}
```

**Detection categories include:** generic openings, editorial commentary, vague claims, fake sources (Truth Layer integrated), repetition, buzzword overuse, inflated language, formulaic structure, excessive formatting, unnatural certainty, lack of personal voice.

**Preferred patterns rewarded:** personal observation, specific details, clear opinion, lessons learned, concrete examples.

### 6. Human Voice Agent (`agents/humanizer`)

**May:** improve clarity, sentence flow, remove generic phrases, make tone natural.

**Must not:** create experiences, add achievements, add metrics, add emotions that did not exist, invent stories.

Consumes writing-quality `improvements` when present.

### 7. AI Writing Critic Agent (`agents/critic`)

**Purpose:** Quality control across truth, authenticity, AI-writing-pattern risk, and engagement potential.

**References:** good/bad posts + ai-like/human-like writing-quality examples.

**Scores**

```json
{
  "truth_score": 0,
  "human_quality_score": 0,
  "ai_pattern_risk": 0,
  "engagement_score": 0,
  "originality": 0,
  "human_quality": 0,
  "engagement_probability": 0,
  "evidence_quality": 0,
  "ai_pattern_score": 0
}
```

**Detects:** generic phrases, weak hooks, unsupported claims, repetition, lack of examples, writing-quality framework patterns

Note: `ai_pattern_risk` / `ai_pattern_score` are higher when more low-quality AI writing patterns are detected (worse). Other scores are “higher is better.” Never labels authorship.

### 8. Engagement Predictor Agent (`agents/engagement_predictor`)

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

## Content Modes (`knowledge/content_modes.json`)

Content modes are voice/structure presets — not persona fabrications.

```json
{
  "modes": {
    "founder": {
      "label": "Founder style",
      "tone": "direct operator",
      "emphasis": ["decisions", "tradeoffs", "lessons from building"],
      "avoid": ["corporate fluff", "fake scale claims"]
    },
    "researcher": {
      "label": "Researcher style",
      "tone": "careful and evidence-led",
      "emphasis": ["claims with sources", "uncertainty where needed"],
      "avoid": ["overconfident generalizations"]
    },
    "engineer": {
      "label": "Engineer style",
      "tone": "precise and practical",
      "emphasis": ["systems", "implementation lessons", "concrete examples"],
      "avoid": ["buzzwords without substance"]
    },
    "career_journey": {
      "label": "Career journey style",
      "tone": "reflective and specific",
      "emphasis": ["transitions", "skills growth", "real milestones"],
      "avoid": ["motivational filler", "invented biography"]
    }
  }
}
```

Writer and Humanizer load the selected mode. Modes never override the `user_memory.json` experience gate.

---

## Source Evidence Layer (`research_sources/`)

Every generated insight may optionally store evidence records on disk and/or in Postgres.

**Record shape**

```json
{
  "id": "",
  "source": "",
  "date": "",
  "confidence": 0.0,
  "extracted_claim": "",
  "post_id": null,
  "pipeline_run_id": null,
  "created_at": ""
}
```

| Field | Meaning |
|---|---|
| `source` | URL or citation label |
| `date` | Publication or access date (ISO preferred) |
| `confidence` | 0.0–1.0 confidence in the claim extraction / applicability |
| `extracted_claim` | Specific claim the source supports |

**Rules**

- Evidence is optional but preferred for research-backed statements.
- Do not invent sources or dates.
- Researcher Agent (Phase 3) writes these; Phase 1 accepts manually supplied evidence in generate requests and persists them.

File layout example:

```text
research_sources/
  README.md
  .gitkeep
  # optional per-run or per-source JSON files once implemented
```

---

## Feedback Learning Loop (`feedback/engagement_feedback.json`)

Track **real** content performance after publishing (manual entry; no LinkedIn scrape required).

**Record shape**

```json
{
  "entries": [
    {
      "post_id": "",
      "recorded_at": "",
      "impressions": 0,
      "likes": 0,
      "comments": 0,
      "reposts": 0,
      "saves": 0,
      "user_rating": 0,
      "notes": "",
      "content_mode": "founder",
      "topic": ""
    }
  ]
}
```

| Field | Purpose |
|---|---|
| `impressions` | Reach |
| `likes` | Positive reactions |
| `comments` | Discussion signal |
| `reposts` | Amplification |
| `saves` | Bookmark / revisit signal |
| `user_rating` | Owner quality rating (e.g. 1–5) |

**Purpose:** allow future optimization (which modes, hooks, and topics correlate with stronger outcomes).

**Phase 1:** schema + API write/read + persist to file/DB.  
**Phase 3:** analytics and optional predictor calibration from aggregated feedback.  
**Non-goal:** claiming automated viral forecasting from sparse early data.

---

## Phase 1 Pipeline (AI Core Engine)

Phase 1 does **not** build the dashboard first. It ships the core engine behind the API (CLI-friendly).

```text
Topic + format + content_mode + user_memory.json (+ optional evidence)
        │
        ▼
  Research Agent
        │
        ▼
  Angle Finder Agent
        │
        ▼
  Strategist Agent
        │
        ▼
   Writer Agent                 ──► draft_v1
        │
        ▼
  Claim Checker (Truth Layer)   ──► grounded draft
        │
        ▼
  AI Writing Quality Analyzer   ──► pattern risk + improvements
        │
        ▼
 Humanizer Agent                ──► draft_v2 (style only)
        │
        ▼
  Critic Agent                  ──► truth / authenticity / pattern risk / engagement
        │
        ▼
 Engagement Predictor           ──► pre-publish weakness report
        │
        ▼
 Persist GeneratedContent + Feedback scores
```

Designer / trend scraping remain Phase 3 unless pulled forward deliberately.

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

1. Topic input + content mode select
2. Generate button
3. Results view (draft + critic + engagement scores + evidence)
4. Edit content
5. Save drafts
6. Manual engagement feedback entry
7. Minimal settings (Ollama URL / model / memory editor)

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
| `GET` | `/modes` | List content modes from `content_modes.json` |
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
| `POST` | `/posts/{id}/evidence` | Attach optional source evidence claims |
| `GET` | `/posts/{id}/evidence` | List evidence for a post |
| `POST` | `/posts/{id}/engagement-feedback` | Record real performance metrics |
| `GET` | `/posts/{id}/engagement-feedback` | Read feedback entries |

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
| PostgreSQL | Users, posts, trends, feedback, carousels, profiles, engagement scores, evidence |
| Filesystem knowledge | `user_memory.json`, rules, modes, good/bad examples |
| `research_sources/` | Optional evidence JSON records |
| `feedback/engagement_feedback.json` | Real performance learning data |
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
| AI evaluation suite | Required Phase 1 quality gates (below) |
| Evaluation fixtures | Critic distinguishes good vs bad example posts |
| API | Generate/save with FakeProvider |
| UI (Phase 2) | Topic → generate → edit → save |

Use a **FakeProvider** in tests — never invent live external APIs.

### AI evaluation suite (`tests/`)

| File | Must verify |
|---|---|
| `test_writer.py` | Prefers first-person authentic writing; rejects fake personal experiences outside `user_memory` |
| `test_humanizer.py` | Prefers / produces first-person authentic voice over corporate AI tone |
| `test_critic.py` | Detects generic AI writing; flags fake experiences; identifies weak hooks |
| `test_engagement_predictor.py` | Returns structured score JSON; flags weak hooks / AI patterns |

These tests are part of the Phase 1 Definition of Done.

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
6. **Content modes** — founder/researcher/engineer/career_journey presets.
7. **Source evidence layer** — optional source/date/confidence/claim per insight.
8. **Feedback learning loop** — manual real metrics for future optimization.
9. **Good/bad post dataset** — critic calibration and regression tests.
10. **Engagement predictor ≠ virality oracle** — pre-publish weakness detection only.
11. **PostgreSQL for persisted generations** — filesystem knowledge for local rules/memory.
