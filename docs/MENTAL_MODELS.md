# Mental Models

Library used by `agents/reasoning/mental_models.py`.

Models are applied as **lenses** over Evidence Graph claims. They do not invent facts.

## Supported models

1. First Principles  
2. Second-order Thinking  
3. Opportunity Cost  
4. Network Effects  
5. Compounding  
6. Flywheel  
7. Pareto  
8. Game Theory  
9. Inversion  
10. Systems Thinking  
11. Prisoner's Dilemma  
12. Diffusion of Innovation  
13. Jobs To Be Done  
14. Porter's Five Forces  
15. SWOT  
16. OODA Loop  
17. Bayesian Thinking  
18. Expected Value  
19. Root Cause Analysis  
20. Decision Trees  

## API

```python
from agents.reasoning import MentalModelEngine, MENTAL_MODELS

engine = MentalModelEngine()
assert "Inversion" in MENTAL_MODELS
apps = engine.apply("pricing power", claims, limit=8)
for app in apps:
    print(app.model, app.observation, app.implication, app.evidence_refs)
```

## Output shape

```json
{
  "model": "Bayesian Thinking",
  "lens": "Update beliefs about pricing power proportionally to new evidence strength.",
  "observation": "Evidence highlights: ...",
  "implication": "Avoid overreacting to weak or unverified claims.",
  "evidence_refs": ["arxiv:1"]
}
```

## Rules

- Prefer models that change the decision, not decorative jargon.
- If the Evidence Graph is empty, models act as **questioning lenses only**.
- Pair Inversion + Bayesian Thinking before high-stakes commitments.
