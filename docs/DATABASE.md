# DATABASE.md — LinkedIn Content Intelligence Engine

## Overview

PostgreSQL is the system of record for users, content, research metadata, trends, writing profiles, carousels, feedback, and engagement predictions.

Local filesystem knowledge files (`knowledge/user_memory.json`, rules, examples) are the **local-first source of truth** for personal context and evaluation datasets. Postgres may store projections/snapshots for queryability.

Qdrant stores embeddings for knowledge memory (Phase 3+). Redis is not a source of truth.

All primary keys are UUIDs unless noted. Timestamps are `timestamptz` in UTC.

---

## Entity Relationship (Logical)

```text
User 1───* Post
User 1───1 WritingProfile
User 1───* GeneratedContent
User 1───* Feedback
User 1───* EngagementFeedback
User 1───* KnowledgeMemory
User 1───* Carousel

Post 1───* GeneratedContent
Post 1───0..1 Carousel
Post 1───* EngagementFeedback
Post *───* ResearchSource   (via post_sources)
Trend 1───* Post            (optional link)

GeneratedContent 1───* Feedback
```

---

## Tables

### `users`

Application user (local single-user friendly; multi-user ready).

| Column | Type | Notes |
|---|---|---|
| `id` | `uuid` PK | |
| `email` | `citext` UNIQUE NULL | Optional for local mode |
| `display_name` | `text` NOT NULL | |
| `timezone` | `text` NOT NULL DEFAULT `'UTC'` | |
| `preferences` | `jsonb` NOT NULL DEFAULT `{}` | UI + model defaults |
| `created_at` | `timestamptz` NOT NULL | |
| `updated_at` | `timestamptz` NOT NULL | |

**Indexes:** unique on `email` where not null.

---

### `writing_profiles`

DB projection of style + allowed experiences. Prefer syncing from `knowledge/user_memory.json`.

| Column | Type | Notes |
|---|---|---|
| `id` | `uuid` PK | |
| `user_id` | `uuid` FK → users UNIQUE | One active profile per user in Phase 1 |
| `tone` | `text` | e.g. technical founder, reflective |
| `voice_traits` | `jsonb` NOT NULL DEFAULT `[]` | |
| `preferred_formats` | `jsonb` NOT NULL DEFAULT `[]` | |
| `allowed_experiences` | `jsonb` NOT NULL DEFAULT `[]` | derived from user memory experiences/projects |
| `background` | `jsonb` NOT NULL DEFAULT `[]` | projection of memory.background |
| `skills` | `jsonb` NOT NULL DEFAULT `[]` | |
| `projects` | `jsonb` NOT NULL DEFAULT `[]` | |
| `preferred_topics` | `jsonb` NOT NULL DEFAULT `[]` | |
| `vocabulary_preferences` | `jsonb` NOT NULL DEFAULT `[]` | |
| `content_preferences` | `jsonb` NOT NULL DEFAULT `[]` | |
| `style` | `jsonb` NOT NULL DEFAULT `{}` | `{first_person, tone, sentence_style, ...}` |
| `memory_snapshot` | `jsonb` NOT NULL DEFAULT `{}` | full copy of user_memory at last sync |
| `banned_topics` | `jsonb` NOT NULL DEFAULT `[]` | |
| `style_rules_override` | `jsonb` NOT NULL DEFAULT `{}` | merges with `knowledge/writing_rules.json` |
| `created_at` | `timestamptz` NOT NULL | |
| `updated_at` | `timestamptz` NOT NULL | |

**Integrity rule:** Writers may only assert lived experiences present in `allowed_experiences` / `memory_snapshot` (sourced from `user_memory.json`).

---

### `posts`

User-facing content records (canonical saved LinkedIn content).

| Column | Type | Notes |
|---|---|---|
| `id` | `uuid` PK | |
| `user_id` | `uuid` FK → users NOT NULL | |
| `topic` | `text` NOT NULL | |
| `format` | `text` NOT NULL | short \| long_form \| carousel_script \| founder_story \| research_summary \| technical_explanation |
| `status` | `text` NOT NULL | draft \| reviewed \| ready \| archived |
| `title` | `text` | optional internal title |
| `body` | `text` NOT NULL | latest accepted body |
| `hook` | `text` | |
| `discussion_question` | `text` | |
| `content_mode` | `text` | founder \| researcher \| engineer \| career_journey |
| `trend_id` | `uuid` FK → trends NULL | |
| `strategy` | `jsonb` | strategist output snapshot |
| `critic_scores` | `jsonb` | latest critic payload |
| `engagement_prediction` | `jsonb` | latest engagement predictor payload |
| `tags` | `jsonb` NOT NULL DEFAULT `[]` | |
| `published_at` | `timestamptz` NULL | manual mark; no auto-publish |
| `created_at` | `timestamptz` NOT NULL | |
| `updated_at` | `timestamptz` NOT NULL | |

**Indexes:** `(user_id, created_at DESC)`, `(user_id, status)`.

---

### `generated_content`

Immutable-ish generation artifacts (pipeline versions).

| Column | Type | Notes |
|---|---|---|
| `id` | `uuid` PK | |
| `user_id` | `uuid` FK → users NOT NULL | |
| `post_id` | `uuid` FK → posts NULL | set when saved/linked |
| `pipeline_run_id` | `uuid` NOT NULL | groups pipeline stages |
| `stage` | `text` NOT NULL | writer \| humanizer \| critic \| engagement_predictor \| final |
| `format` | `text` NOT NULL | |
| `prompt_context` | `jsonb` NOT NULL | topic, memory snapshot, allowed claims |
| `model_provider` | `text` NOT NULL | ollama \| openai \| gemini \| anthropic |
| `model_name` | `text` NOT NULL | |
| `input_text` | `text` | prior stage text |
| `output_text` | `text` | |
| `output_json` | `jsonb` | structured agent output (critic, engagement, slides) |
| `latency_ms` | `int` | |
| `token_usage` | `jsonb` | provider-reported if available |
| `created_at` | `timestamptz` NOT NULL | |

**Indexes:** `(pipeline_run_id)`, `(post_id, created_at)`, `(user_id, created_at DESC)`.

---

### `research_sources`

Trusted sources and optional evidence claims attached to research / posts.

| Column | Type | Notes |
|---|---|---|
| `id` | `uuid` PK | |
| `user_id` | `uuid` FK → users NULL | null = global/system source |
| `source` | `text` NOT NULL | URL or citation label (alias of conceptual `source`) |
| `url` | `text` | Optional normalized URL when `source` is a label |
| `title` | `text` | |
| `source_type` | `text` NOT NULL DEFAULT `'other'` | paper \| report \| article \| data \| other |
| `publisher` | `text` | |
| `published_or_accessed_at` | `date` | maps to evidence `date` |
| `confidence` | `numeric(4,3)` | 0.000–1.000 |
| `extracted_claim` | `text` | specific claim supported by the source |
| `summary` | `text` | |
| `raw_excerpt` | `text` | |
| `metadata` | `jsonb` NOT NULL DEFAULT `{}` | |
| `created_at` | `timestamptz` NOT NULL | |
| `updated_at` | `timestamptz` NOT NULL | |

#### `post_sources` (join)

| Column | Type | Notes |
|---|---|---|
| `post_id` | `uuid` FK → posts | |
| `research_source_id` | `uuid` FK → research_sources | |
| `relevance_note` | `text` | |
| `extracted_claim` | `text` | claim as used in this post (may mirror source) |
| `confidence` | `numeric(4,3)` | per-post applicability override |
| PK | `(post_id, research_source_id)` | |

Filesystem mirror: `research_sources/` JSON files for local-first workflows.

---

### `trends`

Discovered topics from trend analyzer (Phase 3; schema ready earlier).

| Column | Type | Notes |
|---|---|---|
| `id` | `uuid` PK | |
| `topic` | `text` NOT NULL | |
| `trend_level` | `text` NOT NULL | emerging \| rising \| peaking \| saturated |
| `why_it_matters` | `text` | |
| `possible_angles` | `jsonb` NOT NULL DEFAULT `[]` | |
| `target_audience` | `text` | |
| `source_snapshot` | `jsonb` NOT NULL DEFAULT `{}` | HN/Reddit/etc payloads |
| `detected_at` | `timestamptz` NOT NULL | |
| `expires_at` | `timestamptz` | |
| `created_at` | `timestamptz` NOT NULL | |
| `updated_at` | `timestamptz` NOT NULL | |

**Indexes:** `(detected_at DESC)`, `(trend_level, detected_at DESC)`.

---

### `carousels`

Structured carousel documents linked to a post (Phase 3).

| Column | Type | Notes |
|---|---|---|
| `id` | `uuid` PK | |
| `user_id` | `uuid` FK → users NOT NULL | |
| `post_id` | `uuid` FK → posts UNIQUE NULL | |
| `style` | `text` NOT NULL | apple_minimal \| consulting \| research_paper \| modern_startup |
| `slides` | `jsonb` NOT NULL | array of `{slide,title,body,visual,design_instruction}` |
| `export_paths` | `jsonb` NOT NULL DEFAULT `{}` | `{pdf, png[]}` local paths |
| `created_at` | `timestamptz` NOT NULL | |
| `updated_at` | `timestamptz` NOT NULL | |

---

### `engagement_feedback`

Real post performance for the feedback learning loop (manual entry; no LinkedIn scrape).

| Column | Type | Notes |
|---|---|---|
| `id` | `uuid` PK | |
| `user_id` | `uuid` FK → users NOT NULL | |
| `post_id` | `uuid` FK → posts NOT NULL | |
| `recorded_at` | `timestamptz` NOT NULL | when metrics were captured |
| `impressions` | `int` NOT NULL DEFAULT 0 | |
| `likes` | `int` NOT NULL DEFAULT 0 | |
| `comments` | `int` NOT NULL DEFAULT 0 | |
| `reposts` | `int` NOT NULL DEFAULT 0 | |
| `saves` | `int` NOT NULL DEFAULT 0 | |
| `user_rating` | `int` CHECK 1–5 NULL | owner quality rating |
| `content_mode` | `text` | snapshot of mode used |
| `topic` | `text` | snapshot for analytics |
| `notes` | `text` | |
| `raw_payload` | `jsonb` NOT NULL DEFAULT `{}` | extra fields |
| `created_at` | `timestamptz` NOT NULL | |

**Indexes:** `(post_id, recorded_at DESC)`, `(user_id, recorded_at DESC)`, `(content_mode, recorded_at DESC)`.

Filesystem mirror: `feedback/engagement_feedback.json`.

---

### `feedback`

User or agent feedback on content quality — includes critic and engagement predictor outputs.

| Column | Type | Notes |
|---|---|---|
| `id` | `uuid` PK | |
| `user_id` | `uuid` FK → users NOT NULL | |
| `post_id` | `uuid` FK → posts NULL | |
| `generated_content_id` | `uuid` FK → generated_content NULL | |
| `source` | `text` NOT NULL | user \| critic \| humanizer \| engagement_predictor |
| `rating` | `int` CHECK 1–5 NULL | |
| `scores` | `jsonb` | critic or engagement score payload |
| `problems` | `jsonb` NOT NULL DEFAULT `[]` | from engagement predictor |
| `improvements` | `jsonb` NOT NULL DEFAULT `[]` | from engagement predictor |
| `issues` | `jsonb` NOT NULL DEFAULT `[]` | critic issues |
| `notes` | `text` | |
| `created_at` | `timestamptz` NOT NULL | |

**Indexes:** `(post_id)`, `(generated_content_id)`, `(source, created_at DESC)`.

**Engagement predictor `scores` shape**

```json
{
  "overall_score": 0,
  "hook_score": 0,
  "originality_score": 0,
  "specificity_score": 0,
  "discussion_score": 0,
  "ai_pattern_score": 0
}
```

---

### `knowledge_memories`

Long-lived memories for style/research retrieval (Qdrant pointer + metadata in Postgres). Phase 3+.

| Column | Type | Notes |
|---|---|---|
| `id` | `uuid` PK | |
| `user_id` | `uuid` FK → users NOT NULL | |
| `memory_type` | `text` NOT NULL | style_example \| research_chunk \| lesson \| preference \| user_memory_fact |
| `content` | `text` NOT NULL | |
| `metadata` | `jsonb` NOT NULL DEFAULT `{}` | |
| `qdrant_point_id` | `uuid` NULL | set when embedded |
| `source_ref` | `text` | post id, URL, user_memory path, etc. |
| `created_at` | `timestamptz` NOT NULL | |
| `updated_at` | `timestamptz` NOT NULL | |

**Indexes:** `(user_id, memory_type, created_at DESC)`.

---

## Filesystem Knowledge (not Postgres, but part of data design)

| Path | Role |
|---|---|
| `knowledge/user_memory.json` | Canonical personal background / projects / style |
| `knowledge/writing_rules.json` | Voice and structure rules |
| `knowledge/banned_patterns.json` | Rejected phrases/patterns |
| `knowledge/user_style_profile.json` | Optional compact style overrides |
| `knowledge/content_modes.json` | Founder / researcher / engineer / career_journey presets |
| `knowledge/examples/good_posts.json` | Critic / predictor positive references |
| `knowledge/examples/bad_posts.json` | Critic / predictor negative references |
| `research_sources/` | Optional evidence records (source, date, confidence, claim) |
| `feedback/engagement_feedback.json` | Real performance metrics for learning |

Phase 1 may persist generations to Postgres **or** a lightweight local store, but schemas above are the target. Knowledge JSON files are required regardless.

---

## Enumerations (application-level)

Stored as `text` with app validation:

| Field | Allowed values |
|---|---|
| `posts.format` / `generated_content.format` | `short`, `long_form`, `carousel_script`, `founder_story`, `research_summary`, `technical_explanation` |
| `posts.content_mode` / `engagement_feedback.content_mode` | `founder`, `researcher`, `engineer`, `career_journey` |
| `posts.status` | `draft`, `reviewed`, `ready`, `archived` |
| `generated_content.stage` | `writer`, `humanizer`, `critic`, `engagement_predictor`, `final` |
| `trends.trend_level` | `emerging`, `rising`, `peaking`, `saturated` |
| `carousels.style` | `apple_minimal`, `consulting`, `research_paper`, `modern_startup` |
| `feedback.source` | `user`, `critic`, `humanizer`, `engagement_predictor` |
| `research_sources.source_type` | `paper`, `report`, `article`, `data`, `other` |
| `knowledge_memories.memory_type` | `style_example`, `research_chunk`, `lesson`, `preference`, `user_memory_fact` |

---

## Phase Persistence Subsets

### Phase 1 — AI Core Engine (must)

- `users` (or single local default user)
- `writing_profiles` (synced from `user_memory.json`)
- `posts` (including `content_mode`)
- `generated_content` (including `engagement_predictor` stage)
- `feedback` (critic + engagement predictor)
- `research_sources` + `post_sources` (optional evidence attach)
- `engagement_feedback` (manual metrics write/read; learning later)

### Phase 1 — stub / migrate empty OK

- `trends`
- `carousels`
- `knowledge_memories`

### Phase 2 — Web Interface

Same Phase 1 tables; UI reads/writes posts, modes, evidence, and engagement feedback. No new required entities.

### Phase 3 — Advanced

Activate `trends`, `carousels`, `knowledge_memories` + Qdrant; consume `engagement_feedback` for optimization insights.

---

## Qdrant Collections (Phase 3+)

| Collection | Payload highlights |
|---|---|
| `knowledge_memory` | `user_id`, `memory_type`, `postgres_id`, `source_ref` |
| `research_chunks` | `source_id`, `url`, `title` |
| `post_embeddings` | `post_id`, `format`, `status` |
| `example_posts` | `quality` (`good`\|`bad`), `tags` |

Postgres remains canonical for structured state; Qdrant is a retrieval index.

---

## Migration Strategy

- Alembic (or equivalent) migrations under `database/migrations/`
- Seed scripts for:
  - local default user
  - writing profile from `knowledge/user_memory.json`
  - no fake LinkedIn APIs or scraped LinkedIn data

---

## Data Integrity Rules

1. Personal lived experiences may only come from `knowledge/user_memory.json` (and its DB projection).
2. Critic and engagement predictor payloads persisted on `feedback` / `posts` must match ARCHITECTURE schemas.
3. Evidence records must not invent sources, dates, or claims.
4. Engagement feedback is user-entered (or future approved integrations) — never scraped LinkedIn without approval.
5. Soft-delete is out of scope early; use `posts.status = archived`.
6. Do not store cloud provider API keys in the database.
7. Do not store invented LinkedIn credentials or scrape artifacts without an approved approach.
