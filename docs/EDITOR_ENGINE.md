# Editorial Review Engine

## Purpose

Final quality gate before export. Acts like the Editor-in-Chief of The Economist, HBR, Stripe, Linear, or Anthropic.

**The editor never writes. The editor critiques.**

```text
… → LinkedIn Optimizer → EDITORIAL REVIEW → Export
```

Package: `agents/editor/`  
Does not create writing, research, reasoning, or LinkedIn agents.

## Responsibilities

- Review the entire post
- Explain problems
- Suggest improvements
- Decide publish readiness

## Checks

Story flow · logical flow · credibility · evidence · originality · human authenticity · repetition · grammar · sentence/paragraph rhythm · reading fatigue · transitions · trust · confidence · practical usefulness · LinkedIn friendliness

## Modules

| File | Role |
|---|---|
| `editor_pipeline.py` | Orchestrates desk review |
| `editor.py` | Aggregates checkers + score |
| `editor_rules.py` | Editorial standards library |
| `story_reviewer.py` | Arc + usefulness |
| `clarity_checker.py` | Rhythm / fatigue / transitions |
| `consistency_checker.py` | Terminology / tone / tense / contradictions |
| `credibility_checker.py` | Fake experience / invented stats |
| `tone_reviewer.py` | Authenticity / LinkedIn scan |
| `redundancy_detector.py` | Repeated words/phrases/points |
| `copy_editor.py` | Mechanical prose findings |
| `final_publish_gate.py` | Approve / Minor / Major / Reject |
| `schemas.py` | Contracts |

## API

```python
from agents.editor import EditorPipeline, EditorInput

pipe = EditorPipeline()
out = await pipe.run(
    EditorInput(
        text=draft,
        extra={"evidence_refs": ["arxiv:1"]},
        user_memory=memory,
    )
)
report = out.as_report()
decision = out.result.publish_decision
```

## Output

1. Original Draft  
2. Editorial Report  
3. Issues (with **why**)  
4. Suggestions (with **why**)  
5. Approved Draft (only if Approve; never a rewrite)  
6. Publish Decision  

## Rules

- Never invent facts  
- Never change verified evidence  
- Always explain WHY  
- Local only — no UI, cloud, or automation  
