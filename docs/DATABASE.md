# DATABASE.md — LinkedIn Content Intelligence Engine

## Overview

PostgreSQL is the system of record for users, content, research metadata, trends, writing profiles, carousels, and feedback.

Qdrant stores embeddings for knowledge memory (Phase 2+). Redis is not a source of truth.

All primary keys are UUIDs unless noted. Timestamps are `timestamptz` in UTC.

---

## Entity Relationship (Logical)

```text
User 1───* Post
User 1───1 WritingProfile
User 1───* GeneratedContent
User 1───* Feedback
User 1───* KnowledgeMemory
User 1───* Carousel

Post 1───* GeneratedContent
Post 1───0..1 Carousel
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

Learned / configured writing style for a user.

| Column | Type | Notes |
|---|---|---|
| `id` | `uuid` PK | |
| `user_id` | `uuid` FK → users UNIQUE | One active profile per user in MVP |
| `tone` | `text` | e.g. direct, reflective, analytical |
| `voice_traits` | `jsonb` NOT NULL DEFAULT `[]` | adjectives / traits |
| `preferred_formats` | `jsonb` NOT NULL DEFAULT `[]` | |
| `allowed_experiences` | `jsonb` NOT NULL DEFAULT `[]` | **only** inventable-from facts |
| `banned_topics` | `jsonb` NOT NULL DEFAULT `[]` | |
| `vocabulary_notes` | `text` | |
| `example_posts` | `jsonb` NOT NULL DEFAULT `[]` | short exemplars |
| `style_rules_override` | `jsonb` NOT NULL DEFAULT `{}` | merges with `knowledge/writing_rules.json` |
| `created_at` | `timestamptz` NOT NULL | |
| `updated_at` | `timestamptz` NOT NULL | |

Maps to product principle: **no fake experiences** via `allowed_experiences`.

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
| `trend_id` | `uuid` FK → trends NULL | |
| `strategy` | `jsonb` | strategist output snapshot |
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
| `pipeline_run_id` | `uuid` NOT NULL | groups writer/humanizer/critic steps |
| `stage` | `text` NOT NULL | writer \| humanizer \| critic \| final |
| `format` | `text` NOT NULL | |
| `prompt_context` | `jsonb` NOT NULL | topic, profile snapshot, allowed claims |
| `model_provider` | `text` NOT NULL | ollama \| openai \| gemini \| anthropic |
| `model_name` | `text` NOT NULL | |
| `input_text` | `text` | prior stage text |
| `output_text` | `text` | |
| `output_json` | `jsonb` | structured agent output (critic scores, slides, etc.) |
| `latency_ms` | `int` | |
| `token_usage` | `jsonb` | provider-reported if available |
| `created_at` | `timestamptz` NOT NULL | |

**Indexes:** `(pipeline_run_id)`, `(post_id, created_at)`, `(user_id, created_at DESC)`.

---

### `research_sources`

Trusted sources attached to research / posts.

| Column | Type | Notes |
|---|---|---|
| `id` | `uuid` PK | |
| `user_id` | `uuid` FK → users NULL | null = global/system source |
| `url` | `text` | |
| `title` | `text` NOT NULL | |
| `source_type` | `text` NOT NULL | paper \| report \| article \| data \| other |
| `publisher` | `text` | |
| `published_at` | `date` | |
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
| PK | `(post_id, research_source_id)` | |

---

### `trends`

Discovered topics from trend analyzer (Phase 2+; schema ready in MVP).

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

Structured carousel documents linked to a post.

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

### `feedback`

User or agent feedback on content quality.

| Column | Type | Notes |
|---|---|---|
| `id` | `uuid` PK | |
| `user_id` | `uuid` FK → users NOT NULL | |
| `post_id` | `uuid` FK → posts NULL | |
| `generated_content_id` | `uuid` FK → generated_content NULL | |
| `source` | `text` NOT NULL | user \| critic \| humanizer |
| `rating` | `int` CHECK 1–5 NULL | |
| `scores` | `jsonb` | critic score payload |
| `issues` | `jsonb` NOT NULL DEFAULT `[]` | |
| `notes` | `text` | |
| `created_at` | `timestamptz` NOT NULL | |

**Indexes:** `(post_id)`, `(generated_content_id)`.

---

### `knowledge_memories`

Long-lived memories for style/research retrieval (Qdrant pointer + metadata in Postgres).

| Column | Type | Notes |
|---|---|---|
| `id` | `uuid` PK | |
| `user_id` | `uuid` FK → users NOT NULL | |
| `memory_type` | `text` NOT NULL | style_example \| research_chunk \| lesson \| preference |
| `content` | `text` NOT NULL | |
| `metadata` | `jsonb` NOT NULL DEFAULT `{}` | |
| `qdrant_point_id` | `uuid` NULL | set when embedded |
| `source_ref` | `text` | post id, URL, etc. |
| `created_at` | `timestamptz` NOT NULL | |
| `updated_at` | `timestamptz` NOT NULL | |

**Indexes:** `(user_id, memory_type, created_at DESC)`.

---

## Enumerations (application-level)

Stored as `text` with app validation (flexible for MVP):

| Field | Allowed values |
|---|---|
| `posts.format` / `generated_content.format` | `short`, `long_form`, `carousel_script`, `founder_story`, `research_summary`, `technical_explanation` |
| `posts.status` | `draft`, `reviewed`, `ready`, `archived` |
| `generated_content.stage` | `writer`, `humanizer`, `critic`, `final` |
| `trends.trend_level` | `emerging`, `rising`, `peaking`, `saturated` |
| `carousels.style` | `apple_minimal`, `consulting`, `research_paper`, `modern_startup` |
| `feedback.source` | `user`, `critic`, `humanizer` |
| `research_sources.source_type` | `paper`, `report`, `article`, `data`, `other` |
| `knowledge_memories.memory_type` | `style_example`, `research_chunk`, `lesson`, `preference` |

---

## MVP Persistence Subset

Phase 1 **must** implement:

- `users`
- `writing_profiles`
- `posts`
- `generated_content`
- `feedback` (at least critic scores)

Phase 1 **may stub / migrate empty**:

- `research_sources`, `post_sources`
- `trends`
- `carousels`
- `knowledge_memories`

---

## Qdrant Collections (Phase 2+)

| Collection | Payload highlights |
|---|---|
| `knowledge_memory` | `user_id`, `memory_type`, `postgres_id`, `source_ref` |
| `research_chunks` | `source_id`, `url`, `title` |
| `post_embeddings` | `post_id`, `format`, `status` |

Postgres remains canonical; Qdrant is a retrieval index.

---

## Migration Strategy

- Alembic (or equivalent) migrations under `database/migrations/`
- Seed scripts for:
  - local default user
  - empty writing profile
  - optional demo banned-pattern fixtures (not fake LinkedIn APIs)

---

## Data Integrity Rules

1. `writing_profiles.allowed_experiences` is the only source of personal claims the writer may assert as lived experience.
2. Critic `scores` persisted on `feedback` should match the schema in ARCHITECTURE.md.
3. Soft-delete is out of scope for MVP; use `posts.status = archived`.
4. Do not store cloud provider API keys in the database; use environment / secret manager.
