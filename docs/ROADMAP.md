# ROADMAP.md — LinkedIn Content Intelligence Engine

## Guiding Rule

Ship a narrow, excellent MVP before expanding agents and integrations.

Do **not** build everything at once.

---

## Phase 0 — Documentation & Contracts (current)

**Deliverables**

- [x] `docs/PRODUCT.md`
- [x] `docs/ARCHITECTURE.md`
- [x] `docs/DATABASE.md`
- [x] `docs/ROADMAP.md`
- [ ] Root `README.md` (after approval to implement)
- [ ] Knowledge JSON contracts (`writing_rules`, `banned_patterns`, `user_style_profile`)

**Exit criteria**

- Architecture, MVP scope, and development order approved.

---

## Phase 1 — MVP (build next)

### Product scope

1. User dashboard
2. Topic input
3. Ollama connection
4. LinkedIn post generator
5. Human voice rewriting
6. AI quality checker
7. Save generated posts

### Technical scope

| Area | Work |
|---|---|
| Monorepo skeleton | `apps/web`, `apps/api`, `agents/*` stubs, `models/ollama`, `knowledge/*`, `database/` |
| API | health, Ollama status, generate pipeline, CRUD posts, writing profile |
| Agents | writer, humanizer, critic (wired) |
| Agents | researcher, strategist, designer, trend_analyzer (stubs/contracts only) |
| DB | users, writing_profiles, posts, generated_content, feedback |
| Web | dashboard, generate flow, draft + scores view, settings for Ollama |
| Tests | provider fake, banned patterns, API generate/save |
| Docs | README + run instructions |

### Explicitly out of scope

- Live trend scraping
- Full research ingestion
- Carousel PDF/PNG export
- Cloud LLM providers (interface only)
- n8n workflows
- Qdrant-backed memory
- LinkedIn OAuth / publishing

### Exit criteria

- End-to-end: topic → draft → humanize → critique → save works with local Ollama.
- Critic returns five scores + detected issues.
- Banned patterns from knowledge files are enforced or flagged.

---

## Phase 2 — Research & Strategy Depth

- Researcher agent with source capture (`research_sources`)
- Strategist agent inserted before writer
- Qdrant knowledge memory for exemplars and research chunks
- Richer writing profile learning from user feedback
- Async generation jobs via Redis

### Exit criteria

- Posts can cite stored sources.
- Strategy JSON influences hooks/structure measurably.

---

## Phase 3 — Trends & Carousels

- Trend analyzer with RSS / HN / arXiv / GitHub trending connectors
- Trend dashboard and “write about this” action
- Carousel designer agent + slide JSON
- PDF/PNG export to local filesystem
- Design style presets

### Exit criteria

- User can pick a trend, generate a carousel script, and export slides.

---

## Phase 4 — Multi-provider & Automation

- OpenAI / Gemini / Anthropic adapters
- Model routing policy (local preferred, cloud fallback)
- n8n-ready webhook/job endpoints documented with examples
- Optional cloud object storage for exports

### Exit criteria

- Switching providers requires config only, not agent rewrites.
- External automation can trigger and fetch generations.

---

## Phase 5 — Style Intelligence & Quality Hardening

- Continuous style profile updates from accepted edits
- Stronger anti-hallucination checks for personal claims
- Evaluation harness (golden posts, regression on banned patterns)
- Performance/latency budgets per pipeline stage

---

## Development Order (Phase 1 implementation)

When coding is approved, implement in this order:

1. **Repo skeleton & tooling**  
   Package layout, lint/test runners, env samples, Docker Compose for Postgres (+ Redis optional).

2. **Knowledge contracts**  
   `writing_rules.json`, `banned_patterns.json`, seed `user_style_profile.json`, example posts.

3. **Database migrations**  
   MVP tables first; empty migrations OK for deferred entities.

4. **Model provider interface + Ollama adapter**  
   Health check, generate text, FakeProvider for tests.

5. **Writer agent**  
   Format-aware prompts; inject allowed experiences; apply writing rules.

6. **Humanizer agent**  
   Rewrite pass with authenticity checklist.

7. **Critic agent**  
   Structured scores + rule-based banned pattern detection (hybrid: LLM + deterministic).

8. **Orchestrator + API routes**  
   Sync pipeline for MVP; persist `generated_content` and `posts`.

9. **Web dashboard**  
   Status, topic form, results panel, save action, minimal settings.

10. **Tests + README**  
    Contract tests and local runbook.

Do not start trend connectors, carousel export, or cloud providers before the MVP loop is stable.

---

## Risk Register

| Risk | Mitigation |
|---|---|
| Local models produce generic prose | Strong knowledge rules + humanizer + critic gate |
| Models invent personal stories | Allowed-experiences context gate + critic claim check |
| Ollama unavailable | Clear UI status; do not fake successful generations |
| Scope creep into full agent suite | Phase gates in this roadmap |
| Over-dependence on one mega-prompt | Keep agents separate with schemas |

---

## Definition of Done (any phase)

- Documented behavior matches implemented behavior
- Types/schemas enforced
- Tests for new logic
- No invented external integrations
- README / docs updated for user-facing changes
