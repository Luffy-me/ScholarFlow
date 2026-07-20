# Quality Scoring (LinkedIn Optimizer)

Defined in `agents/linkedin_optimizer/post_score.py`.

## Dimensions

| Dimension | Meaning |
|---|---|
| Hook | Stop-scroll quality of opening |
| Novelty | Non-obvious / counterintuitive signal |
| Evidence | Evidence Graph refs present; fake claims penalized |
| Reasoning | Trade-offs / constraints / causal language |
| Originality | Non-generic phrasing |
| Readability | Sentence/paragraph/formatting fitness |
| Authority | Grounded voice + evidence support |
| Practical Value | Frameworks, metrics, playbooks |
| Discussion Potential | Questions / debate prompts |
| **Overall** | Aggregate (+ excellence bonus) |

## Publish gate

```text
minimum_publish_score = 95
publish_ready = overall >= 95
```

Hard gates:

- Fake experience claims → overall capped at 40  
- Generic AI phrasing → overall capped at 70  

## Related

- `docs/LINKEDIN_OPTIMIZER.md`
- `docs/ENGAGEMENT_ESTIMATION.md`
- Existing upstream scorers (`agents/quality`, `agents/writing_quality`) remain unchanged; this layer adds LinkedIn-specific publish scoring after generation.
