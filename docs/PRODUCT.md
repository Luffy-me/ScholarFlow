# PRODUCT.md — LinkedIn Content Intelligence Engine

## Vision

Build a **local-first AI system** that helps professionals create authentic, research-backed LinkedIn thought leadership content.

This is **not** a generic AI post generator.

The product behaves like a professional content strategist:

1. Discover what topics are gaining attention.
2. Analyze why certain content performs.
3. Research information from trusted sources.
4. Find unique angles.
5. Generate human-like first-person LinkedIn posts.
6. Create professional carousel designs.
7. Critique content quality before publishing.
8. Learn the user’s writing style over time.

The goal is to help users turn **real knowledge, experiences, and research** into high-quality LinkedIn content.

---

## Problem Statement

Most LinkedIn AI tools produce content that:

- Sounds generic and corporate
- Invents fake personal experiences
- Lacks research or evidence
- Uses detectable AI patterns
- Ignores the user’s voice and expertise

Professionals need a system that:

- Protects authenticity
- Grounds claims in sources
- Preserves first-person voice rooted in real context
- Improves draft quality before publishing
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

unless the information exists in the user’s profile, writing profile, or explicitly provided context.

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
| Content strategy | Choose audience, hook, opinion, structure |
| Research grounding | Attach sources and evidence to drafts |
| Post generation | Multiple LinkedIn formats |
| Humanization | Rewrite drafts into authentic voice |
| Quality critique | Score originality, human quality, engagement, evidence, AI patterns |
| Carousel design | Structured multi-slide document posts + export |
| Style learning | Persist and improve user writing profile over time |
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

## MVP Product Scope (Phase 1)

Phase 1 deliberately excludes trend scraping, carousel export, full research pipelines, and multi-provider orchestration maturity.

**In scope**

1. User dashboard
2. Topic input
3. Ollama connection
4. LinkedIn post generator
5. Human voice rewriting
6. AI quality checker
7. Save generated posts

**Out of scope for MVP**

- Automated trend ingestion (RSS, HN, Reddit, arXiv, GitHub)
- Full research agent pipeline
- Carousel PDF/PNG export
- Cloud provider adapters beyond a clean interface stub
- n8n automation flows
- Multi-user auth / SaaS billing
- Style learning from published feedback loops (beyond a static profile seed)

---

## Success Criteria (MVP)

A user can:

1. Open the dashboard and enter a topic.
2. Confirm Ollama is reachable and a model is selected.
3. Generate a first-person LinkedIn draft that avoids banned AI patterns.
4. Run human-voice rewriting on the draft.
5. Receive critic scores with actionable issues.
6. Save the post (and scores) for later review.

Quality bar:

- Drafts default to first person when user context allows.
- Critic flags banned phrases and weak hooks.
- No invented personal achievements without profile evidence.

---

## Non-Goals

- Auto-posting to LinkedIn without explicit user action
- Guaranteeing viral performance
- Replacing the user’s judgment or expertise
- Building a closed SaaS-only product (local-first / open-source first)

---

## Knowledge Assets

Product behavior is constrained by versioned knowledge files:

| File | Role |
|---|---|
| `knowledge/writing_rules.json` | Style, structure, and voice rules |
| `knowledge/banned_patterns.json` | Phrases and patterns to reject |
| `knowledge/user_style_profile.json` | Per-user tone, vocabulary, examples |
| `knowledge/examples/` | Few-shot exemplars of good / bad posts |

These files are part of the product contract, not optional prompts.

---

## Ethical Constraints

- Do not fabricate credentials, metrics, or personal history.
- Cite or attribute research claims when sources are available.
- Prefer uncertainty language over false certainty.
- Keep user content and style profiles local by default.
