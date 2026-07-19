# Verified Experience Memory + Content Angle Intelligence

## Verified Experience Memory System

`agents/memory_builder/` converts **user-provided** experiences into verified memories.

Rules:
- Never create experiences automatically
- Store only user-approved facts in `verified_experiences`
- Pending facts stay in `pending_experiences` until approve/reject
- Generation/grounding may reuse only approved reusable facts

### Schema (`knowledge/user_memory.json`)

Key additions:
- `schema_version`: `2.0`
- `verified_experiences[]`: `{id, statement, category, source, approved, approved_at, tags, reusable, related_projects}`
- `pending_experiences[]`: same shape, `approved=false`
- `memory_policy.never_auto_create_experiences = true`

### API

- `GET /api/v1/memory/verified`
- `GET /api/v1/memory/pending`
- `POST /api/v1/memory/experiences/propose`
- `POST /api/v1/memory/experiences/approve`
- `POST /api/v1/memory/experiences/reject`

## Content Angle Agent

`agents/angle_finder/` generates multiple unique LinkedIn angles before writing.

Output:
```json
{
  "angles": [
    {
      "type": "",
      "hook": "",
      "reason": "",
      "target_audience": ""
    }
  ]
}
```

## Pipeline

```text
Research
  ↓
Angle Finder
  ↓
Strategist
  ↓
Writer
  ↓
Claim Checker
  ↓
AI Writing Quality Analyzer
  ↓
Humanizer
  ↓
Critic
  ↓
Engagement Predictor
```

## Tests

- approved experiences reused
- unapproved experiences rejected
- multiple angles generated
- memory builder never auto-approves

See also [WRITING_QUALITY.md](./WRITING_QUALITY.md).
