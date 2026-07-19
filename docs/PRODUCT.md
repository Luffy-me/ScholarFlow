# PRODUCT.md — LinkedIn Content Intelligence Engine

## Vision

Build a **local-first AI system** that helps professionals create authentic, research-backed LinkedIn thought leadership content.

This is **not** a generic AI text generator.

The product behaves like a **content intelligence system**:

```text
Research → Trend Analysis → Insight Engine → Angle Finder → Strategize →
Write → Claim Check → Writing Quality Analyze → Humanize → Critique → Predict → Export
```

Concrete behaviors:

1. Discover what topics are gaining attention.
2. Research information from trusted sources.
3. Generate an original insight (belief contrast + actionable takeaway) before writing.
4. Analyze angles and decide strategy.
5. Generate human-like first-person LinkedIn posts.
6. Ground claims against verified experience memory (Truth Layer).
7. Score low-quality AI writing pattern risk (not AI detection / authorship claims).
8. Humanize drafts into authentic voice without inventing facts.
9. Critique truth, authenticity, pattern risk, and engagement potential.
10. Predict engagement quality (weakness detection, not virality).

The goal is to help users turn **real knowledge, experiences, and research** into high-quality LinkedIn content.

---

## Problem Statement

Most LinkedIn AI tools produce content that:

- Sounds generic and corporate
- Invents fake personal experiences
- Lacks research or evidence
- Uses detectable AI patterns
- Ignores the user’s voice and expertise
- Ships weak hooks without a pre-publish quality gate

Professionals need a system that:

- Protects authenticity
- Grounds claims in sources
- Preserves first-person voice rooted in real context
- Improves draft quality before publishing
- Flags weak content before it goes live
- Runs locally when possible (privacy + cost control)

---

## Product Principles

### 1. Human-first writing

Every generated post should feel written by a real person.

**Default style**

- First person (“I”, “my”, “we”) whenever appropriate
- Personal observations
- Lessons learned
- Experiments
- Opinions
- Specific examples

**Avoid**

- Generic AI introductions
- Corporate language
- Fake enthusiasm
- Empty motivational statements

**Never generate** (unless there is a very specific, justified reason):

- “In today’s rapidly evolving world…”
- “Artificial intelligence is revolutionizing…”
- “It is important to note…”
- “The future of…”

**Write like**

> “I spent the last few weeks testing local AI models, and one thing surprised me…”

**Not**

> “Artificial intelligence is transforming the technology landscape.”

### 2. No fake experiences

The system must **never invent user experiences**.

Never write claims such as:

- “I built a million-user product.”
- “I tested this with thousands of customers.”
- “I discovered during my research…”

unless the information exists in **`knowledge/user_memory.json`** (or an explicitly provided, session-scoped note that is written into memory).

If personal experience is unavailable, prefer:

- “One interesting pattern I noticed…”
- “Recent research suggests…”
- “After analyzing…”

### 3. Research-backed content

Posts should be grounded in:

- Data
- Papers
- Reports
- Articles
- Real examples

Unsupported claims should be flagged by the critic agent and avoided by the writer.

### 4. Local-first AI

Prioritize local models for privacy, cost, and offline capability.

**Primary AI**

- Ollama
- Qwen models
- DeepSeek models

**Supported providers (pluggable)**

- Local (Ollama)
- OpenAI API
- Gemini API
- Anthropic API

### 5. Pre-publish quality gates

Before content is treated as final:

1. **Claim Checker** removes or rejects ungrounded personal claims.
2. **AI Writing Quality Analyzer** scores pattern risk / specificity / originality and lists improvements. It does **not** claim content was written by AI.
3. **Critic** evaluates truth, human authenticity, AI writing patterns, and engagement potential.
4. **Engagement Predictor** scores hook/originality/specificity/discussion potential and lists concrete problems + improvements.

The predictor does **not** claim viral success. It identifies weak content early.

---

## Target Users

| Persona | Need |
|---|---|
| Founders / operators | Share lessons without sounding promotional |
| Engineers / researchers | Translate technical work into accessible posts |
| Consultants / strategists | Publish opinionated, evidence-backed takes |
| Creators building authority | Maintain a consistent human voice at scale |

---

## Core Capabilities (Full Product)

| Capability | Description |
|---|---|
| Trend discovery | Find emerging topics before saturation |
| Research grounding | Attach sources and evidence to drafts |
| Content strategy | Choose audience, hook, opinion, structure |
| Post generation | Multiple LinkedIn formats |
| Humanization | Rewrite drafts into authentic voice |
| Writing quality framework | Detect low-quality AI writing patterns; reward specific human voice |
| Quality critique | Score truth, authenticity, pattern risk, engagement |
| Engagement prediction | Pre-publish weakness detection with improvements |
| Feedback learning | Capture real post performance for future optimization |
| Source evidence | Optional claims with source, date, confidence |
| Content modes | Founder / researcher / engineer / career journey styles |
| Carousel design | Structured multi-slide document posts + export |
| User memory | Ground writing in real background, projects, style |
| Local model routing | Prefer Ollama; allow cloud fallback |

---

## Content Formats

- Short post
- Long-form post
- Carousel script
- Founder story
- Research summary
- Technical explanation

---

## Content Modes

Generation can target a **content mode** (voice/structure preset), defined in `knowledge/content_modes.json`:

| Mode | Intent |
|---|---|
| `founder` | Operator lessons, decisions, tradeoffs, building in public |
| `researcher` | Evidence-led takes, careful claims, source-aware framing |
| `engineer` | Technical clarity, systems thinking, concrete implementation lessons |
| `career_journey` | Career narrative, transitions, skills growth, reflective milestones |

Modes change tone and structure. They do **not** invent experiences. Personal claims still require `user_memory.json`.

---

## Source Evidence Layer

Every generated insight may optionally attach evidence:

- `source` — URL or citation label
- `date` — publication or access date
- `confidence` — 0–1 or labeled band (low / medium / high)
- `extracted_claim` — the specific claim the source supports

Stored under `research_sources/` (files) and/or Postgres `research_sources` / claim join records. Unsupported claims remain discouraged; evidence is preferred when available.

---

## Feedback Learning Loop

After publishing (manual entry — no LinkedIn scraping required), users can record real performance in `feedback/engagement_feedback.json` (and DB projection):

- impressions
- likes
- comments
- reposts
- saves
- user rating

Purpose: enable **future** optimization (which modes/hooks/topics perform) without claiming automated virality prediction from incomplete data.

---

## Delivery Phases (Product View)

### Phase 1 — AI Core Engine (no dashboard-first)

1. Ollama connection
2. Model abstraction layer
3. Writer Agent (content mode aware)
4. Human Voice Agent
5. Critic Agent
6. Engagement Predictor Agent
7. Save generated content
8. Knowledge contracts: user memory, content modes, good/bad examples
9. Source evidence schema + optional claim attachment
10. Feedback learning schema (`engagement_feedback.json`) — write/read ready; learning models later

### Phase 2 — Simple Web Interface

- Topic input + content mode select
- Generate button
- Results view (draft + critic + engagement scores + optional evidence)
- Edit content
- Save drafts
- Manual engagement feedback entry

### Phase 3 — Advanced Features

- Trend discovery
- Source analysis (full research agent)
- Feedback-driven optimization insights
- Carousel generation
- Browser extension
- Analytics
---

## Success Criteria (Phase 1 — AI Core)

A developer / early user can:

1. Confirm Ollama is reachable and a model is selected (CLI or API).
2. Provide a topic (+ optional format + content mode) with `user_memory.json` loaded.
3. Run Writer → Humanizer → Critic → Engagement Predictor.
4. Receive structured critic scores and engagement prediction JSON.
5. Optionally attach source evidence claims to insights.
6. Persist generated content, scores, and (later) manual engagement feedback.

Quality bar:

- Drafts default to first person when user memory allows.
- Content mode changes style without inventing biography.
- Critic uses `good_posts.json` / `bad_posts.json` as references.
- Engagement predictor returns problems + improvements (not vanity “viral” claims).
- No invented personal achievements outside `user_memory.json`.
- Feedback schema exists for real performance tracking (learning loop consumes it later).

---

## Non-Goals

- Auto-posting to LinkedIn without explicit user action
- Guaranteeing viral performance
- Scraping LinkedIn without an approved approach
- Invented LinkedIn integrations or fake APIs
- Replacing the user’s judgment or expertise
- Building a closed SaaS-only product (local-first / open-source first)

---

## Knowledge Assets

Product behavior is constrained by versioned knowledge files:

| File / path | Role |
|---|---|
| `knowledge/writing_rules.json` | Style, structure, and voice rules |
| `knowledge/banned_patterns.json` | Phrases and patterns to reject |
| `knowledge/user_style_profile.json` | Compact style overrides (optional companion to memory) |
| `knowledge/user_memory.json` | **Canonical** real background, projects, experiences, tone |
| `knowledge/content_modes.json` | Founder / researcher / engineer / career journey presets |
| `knowledge/examples/good_posts.json` | Reference exemplars of strong posts |
| `knowledge/examples/bad_posts.json` | Reference exemplars of weak / AI-like posts |
| `research_sources/` | Optional evidence records (source, date, confidence, claim) |
| `feedback/engagement_feedback.json` | Real post performance for learning loop |

These files are part of the product contract, not optional prompts.

**Critical rule:** Only experiences present in `user_memory.json` may be used as lived personal claims.
---

## Ethical Constraints

- Do not fabricate credentials, metrics, or personal history.
- Cite or attribute research claims when sources are available.
- Prefer uncertainty language over false certainty.
- Keep user content and memory local by default.
- Never scrape LinkedIn without an approved approach.
- Never invent LinkedIn API integrations.
