# Framework Engine

`agents/reasoning/framework_builder.py` automatically builds **reusable frameworks** from topic + Evidence Graph context.

## Framework kinds

| Kind | Use |
|---|---|
| 3-Step Framework | Operating loop |
| 5-Step Framework | Analysis scaffold |
| Decision Matrix | Option comparison |
| Flywheel | Reinforcing loop |
| Pyramid | Governing thought → pillars → facts |
| Checklist | Quality gate |
| Roadmap | 90-day plan with kill-criteria |

## API

```python
from agents.reasoning import FrameworkBuilder, FRAMEWORK_KINDS

builder = FrameworkBuilder()
frameworks = builder.build("RAG evaluation", claims, hypotheses=hyps, tradeoffs=tradeoffs)
assert "Flywheel" in FRAMEWORK_KINDS
```

## Example output

```json
{
  "name": "RAG evaluation 3-Step Operating Loop",
  "kind": "3-Step Framework",
  "steps": [
    "1. Diagnose with Evidence Graph claims for RAG evaluation",
    "2. Account for: …",
    "3. Decide and instrument a feedback metric"
  ],
  "description": "Compact operating loop grounded in evidence.",
  "reusable": true,
  "evidence_refs": ["arxiv:1"]
}
```

## Rules

- Steps that mention facts must be claim-linked via `evidence_refs`.
- Empty evidence still yields frameworks, but steps explicitly demand evidence collection.
- Frameworks are thoughts/tools — not finished articles or LinkedIn posts.
