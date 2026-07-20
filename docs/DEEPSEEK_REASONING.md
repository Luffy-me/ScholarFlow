# DeepSeek Reasoning Layer

## Purpose

Use **DeepSeek** for analysis, reasoning, criticism, and insight generation.  
Use **Qwen** for human writing voice.

This is not a fine-tune. It is model routing across pipeline stages.

## Provider layout

```text
models/
  deepseek_provider.py   # DeepSeek provider (Ollama-backed)
  router.py              # DeepSeek vs Qwen stage routing
  ollama/provider.py     # shared Ollama transport
  deepseek/presets.py    # default DeepSeek tags
```

## Routing

| Family | Stages |
|---|---|
| DeepSeek | research, trend analysis, insight engine, claim checker, critic, engagement predictor, debate critic |
| Qwen | writer, humanizer, debate rewrite |

## Configuration

```bash
WRITER_MODEL=qwen3:8b
HUMANIZER_MODEL=qwen3:8b

RESEARCH_MODEL=deepseek
INSIGHT_MODEL=deepseek
CRITIC_MODEL=deepseek
PREDICTOR_MODEL=deepseek

DEEPSEEK_MODEL=deepseek-r1:7b
DEBATE_MODE=true
```

Alias `deepseek` resolves to `DEEPSEEK_MODEL` (default `deepseek-r1:7b`).

## Insight Engine (DeepSeek)

```json
{
  "hidden_pattern": "",
  "common_belief": "",
  "contrarian_view": "",
  "why_it_matters": "",
  "supporting_reasoning": "",
  "reader_takeaway": "",
  "originality_score": 0
}
```

## Debate Mode

For high-quality posts:

1. **Qwen** writes draft  
2. **DeepSeek** critic reviews generic ideas, weak arguments, missing evidence, originality, AI writing patterns  
3. **Qwen** rewrites from critique  
4. **DeepSeek** gives final score (`accepted` / reject generic)

Generic-dominated drafts are rejected (`generic_rejected`).

## Pipeline

```text
Research (DeepSeek)
  ↓
Trend Analysis (DeepSeek)
  ↓
Insight Engine (DeepSeek)
  ↓
Angle Finder (DeepSeek)
  ↓
Strategist (DeepSeek)
  ↓
Writer (Qwen)
  ↓
Debate Mode (Qwen ↔ DeepSeek)
  ↓
Claim Checker (DeepSeek family / deterministic gate)
  ↓
AI Writing Quality Analyzer
  ↓
Humanizer (Qwen)
  ↓
Critic (DeepSeek)
  ↓
Engagement Predictor (DeepSeek)
```
