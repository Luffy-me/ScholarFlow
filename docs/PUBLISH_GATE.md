# Publish Gate

`agents/editor/final_publish_gate.py`

## Decisions

| Decision | When |
|---|---|
| **Approve** | Overall ≥ 88, no critical issues, no major issues |
| **Needs Minor Revision** | Minor issues and/or borderline score |
| **Needs Major Revision** | Major issues, weak clarity, or overall < 75 with majors |
| **Reject** | Critical credibility failures, trust < 40, or evidence < 35 |

## Blocking conditions (Reject)

- Fake / unverified personal experience  
- Invented statistics without Evidence Graph refs  
- Unsourced invented anecdotes  
- Trust/evidence collapse  

## Output fields

```json
{
  "decision": "Needs Major Revision",
  "rationale": ["...", "Score snapshot: ..."],
  "blocking_issues": ["NO_FAKE_EXPERIENCE: ..."],
  "score_overall": 62
}
```

## Approved draft policy

The editor **does not rewrite**.

- `Approve` → `approved_draft = original_draft`  
- Any other decision → `approved_draft = ""`  
