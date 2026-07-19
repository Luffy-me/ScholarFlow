# Reasoning Engine

## Purpose

ScholarFlow should not merely summarize information. The Reasoning Engine produces **thoughts** — structured, falsifiable reasoning — in the style of a McKinsey consultant, research scientist, product strategist, economist, and founder.

Independent subsystem: `agents/reasoning/`  
No UI. No cloud. Deterministic. Local-only.

## Rules

1. **Never hallucinate facts** — statements must reference the Evidence Graph.
2. **Always keep competing hypotheses** — never assume one explanation.
3. **Challenge every conclusion** via the Counter Argument Engine.
4. **Reflect** before finalizing (“What did we overlook?”).
5. Output **thoughts**, not articles.

## Inputs

| Input | Source |
|---|---|
| Evidence Graph | `knowledge.evidence.EvidenceStore` / claim dicts |
| Knowledge Graph | `knowledge_graph.KnowledgeGraph` |
| Research | `ResearchBrief` / dict |
| Trend Data | `TrendSignal` list / dict |
| Opportunity Engine | `ContentOpportunity` / dict |

## Pipeline

```text
Research
  ↓
Extract assumptions
  ↓
Identify contradictions
  ↓
Generate hypotheses
  ↓
Apply first-principles reasoning
  ↓
Apply mental models
  ↓
Generate frameworks
  ↓
Evaluate trade-offs
  ↓
Generate counterarguments
  ↓
Produce insights
  ↓
Confidence scoring
  ↓
Reflection
```

## Modules

| File | Role |
|---|---|
| `reasoning_pipeline.py` | Orchestrates the full chain |
| `hypothesis_generator.py` | Competing hypotheses |
| `first_principles.py` | Fundamentals from evidence |
| `mental_models.py` | Fixed model library |
| `framework_builder.py` | Reusable frameworks |
| `counter_argument.py` | Challenge conclusions |
| `decision_engine.py` | Expected-value decisions |
| `analogy_engine.py` | Cautious analogies |
| `causal_reasoning.py` | Candidate causal links |
| `systems_thinking.py` | Stocks / flows / leverage |
| `tradeoff_analysis.py` | Explicit trade-offs |
| `scenario_simulator.py` | Best / expected / worst |
| `reflection.py` | Overlooked + tighten |
| `confidence_engine.py` | Evidence / reasoning / novelty / confidence |
| `schemas.py` | Thought contracts |

## API

```python
from agents.reasoning import ReasoningPipeline, ReasoningInput
from knowledge.evidence import EvidenceStore

store = EvidenceStore(path)
store.upsert({
    "claim": "Evaluation loops beat model size for product quality",
    "supporting_sources": ["arxiv:1"],
    "confidence": 0.9,
    "verified": True,
})

engine = ReasoningPipeline()
result = await engine.run(
    ReasoningInput(
        topic="local LLM evaluation",
        extra={
            "evidence": store,
            "research": {"topic": "local LLM evaluation", "open_questions": ["What metric?"]},
            "trends": [{"trend": "Teams shifting to eval harnesses", "momentum": 0.7, "confidence": 0.6}],
            "opportunity": {"score": 72, "target_audience": "engineers", "recommended_angle": "pain points"},
        },
    )
)
thoughts = result.as_thoughts()
```

## Insight contract

Every insight answers:

- Why?
- Why now?
- What changes?
- Who benefits?
- Who loses?
- What happens next?
- What are the risks?
- What is missing?

## Confidence

Every insight / packet receives:

- `evidence_quality`
- `reasoning_quality`
- `novelty`
- `confidence`

Missing Evidence Graph refs cap confidence.

## Related docs

- `docs/MENTAL_MODELS.md`
- `docs/FRAMEWORK_ENGINE.md`
- `docs/KNOWLEDGE_GRAPH.md`
- `docs/RESEARCH_PIPELINE.md`
