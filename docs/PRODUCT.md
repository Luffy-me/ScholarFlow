# PRODUCT.md — LinkedIn Content Intelligence Engine

## Vision

Build a **local-first AI system** that helps professionals create authentic, research-backed LinkedIn thought leadership content.

This is **not** a generic AI text generator.

The product behaves like a **content intelligence system**:

```text
Research → Analyze → Strategize → Write → Humanize → Critique → Improve → Export
```

Concrete behaviors:

1. Discover what topics are gaining attention.
2. Research information from trusted sources.
3. Analyze angles and decide strategy.
4. Generate human-like first-person LinkedIn posts.
5. Humanize drafts into authentic voice.
6. Critique content quality before publishing.
7. Predict engagement quality (weakness detection, not virality).
8. Improve drafts from critique and prediction signals.
9. Export final content (and later carousels).
10. Learn from the user’s real background and writing style over time.

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

1. **Critic** checks writing quality, evidence, and AI patterns.
2. **Engagement Predictor** scores hook/originality/specificity/discussion potential and lists concrete problems + improvements.

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
| Quality critique | Score originality, human quality, evidence, AI patterns |
| Engagement prediction | Pre-publish weakness detection with improvements |
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

## Delivery Phases (Product View)

### Phase 1 — AI Core Engine (no dashboard-first)

1. Ollama connection
2. Model abstraction layer
3. Writer Agent
4. Human Voice Agent
5. Critic Agent
6. Engagement Predictor Agent
7. Save generated content

### Phase 2 — Simple Web Interface

- Topic input
- Generate button
- Results view (draft + critic + engagement scores)
- Edit content
- Save drafts

### Phase 3 — Advanced Features

- Trend discovery
- Source analysis
- Carousel generation
- Browser extension
- Analytics

---

## Success Criteria (Phase 1 — AI Core)

A developer / early user can:

1. Confirm Ollama is reachable and a model is selected (CLI or API).
2. Provide a topic (+ optional format) with `user_memory.json` loaded.
3. Run Writer → Humanizer → Critic → Engagement Predictor.
4. Receive structured critic scores and engagement prediction JSON.
5. Persist generated content and scores to the database / local store.

Quality bar:

- Drafts default to first person when user memory allows.
- Critic uses `good_posts.json` / `bad_posts.json` as references.
- Engagement predictor returns problems + improvements (not vanity “viral” claims).
- No invented personal achievements outside `user_memory.json`.

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

| File | Role |
|---|---|
| `knowledge/writing_rules.json` | Style, structure, and voice rules |
| `knowledge/banned_patterns.json` | Phrases and patterns to reject |
| `knowledge/user_style_profile.json` | Compact style overrides (optional companion to memory) |
| `knowledge/user_memory.json` | **Canonical** real background, projects, experiences, tone |
| `knowledge/examples/good_posts.json` | Reference exemplars of strong posts |
| `knowledge/examples/bad_posts.json` | Reference exemplars of weak / AI-like posts |

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
