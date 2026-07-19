# Engagement Estimation

`agents/linkedin_optimizer/engagement_estimator.py` estimates LinkedIn outcomes for an **existing** draft.

## Probabilities

- Save probability  
- Comment probability  
- Share probability  
- Follower probability  
- Read-through probability  

Plus a **confidence interval** (`confidence_low`, `confidence_high`) and a `why` list explaining drivers.

## Signals used

- LinkedIn post score dimensions (practical value, discussion, novelty, authority)
- Hook stop-scroll strength
- Structure / readability
- Length band and jargon density
- Presence of questions

## Notes

- Estimates are local heuristics — not live LinkedIn analytics.
- They complement (do not replace) `EngagementPredictorAgent`.
- Interval widens when evidence quality is low.

## Example

```json
{
  "save_probability": 0.42,
  "comment_probability": 0.31,
  "share_probability": 0.18,
  "follower_probability": 0.12,
  "read_through_probability": 0.55,
  "confidence_low": 0.22,
  "confidence_high": 0.48,
  "why": ["A question in the draft raises comment probability."]
}
```
