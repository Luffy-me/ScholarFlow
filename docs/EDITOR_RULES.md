# Editor Rules

Source: `agents/editor/editor_rules.py`

Standards inspired by Economist / HBR / Stripe / Linear / Anthropic desks.

## Rule catalog (selected)

| Code | Category | Intent |
|---|---|---|
| `STORY_ARC` | story | context → tension → insight → implication |
| `LOGIC_LINKS` | flow | causal/contrastive glue |
| `EVIDENCE_REQUIRED` | credibility | support non-trivial claims |
| `NO_FAKE_EXPERIENCE` | credibility | verified memory only |
| `NO_INVENTED_STATS` | credibility | no unsourced numbers |
| `ORIGINALITY` | originality | no generic AI filler |
| `HUMAN_VOICE` | tone | concrete operator voice |
| `NO_REPETITION` | redundancy | cut echoed points |
| `SENTENCE_RHYTHM` | clarity | vary / shorten long clauses |
| `PARAGRAPH_RHYTHM` | clarity | mobile-scannable blocks |
| `TRANSITIONS` | flow | purposeful bridges |
| `TERMINOLOGY` | consistency | one term per concept |
| `TONE_CONSISTENCY` | consistency | one audience voice |
| `TENSE_CONSISTENCY` | consistency | controlled tense |
| `WEAK_OPENING` / `WEAK_ENDING` | copy | earn attention / land meaning |
| `PASSIVE_VOICE` | copy | prefer agency |
| `PRACTICAL_USE` | practicality | usable distinction |
| `LINKEDIN_SCAN` | linkedin | feed fitness |
| `EXPLAIN_WHY` | process | every note has a reason |

Every issue emitted by checkers includes `why` and `suggestion`.
