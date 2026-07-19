# Model Routing

## Principle

**No agent imports a concrete model.**

Agents declare required capabilities. The orchestrator selects a provider family and model.

## Files

- `models/capabilities.py` — capability enum + stage mapping
- `models/orchestrator.py` — capability → provider selection
- `models/router.py` — DeepSeek/Qwen family routing + call recording
- `models/deepseek_provider.py` — DeepSeek backend (Ollama-hosted)

## Capabilities

| Capability | Preferred family |
|---|---|
| Reasoning | DeepSeek |
| Critique | DeepSeek |
| Extraction | DeepSeek |
| Ranking | DeepSeek |
| Research | DeepSeek |
| Trend detection | DeepSeek |
| Writing | Qwen |
| Summarization | Qwen |
| Classification | Qwen |

## Example

```python
from models.capabilities import Capability
from models.orchestrator import ModelOrchestrator

orch = ModelOrchestrator(fake=False)
writer = orch.select_for_capability(Capability.WRITING).provider
critic = orch.select_for_capability(Capability.CRITIQUE).provider
```

## Config aliases

```bash
WRITER_MODEL=qwen3:8b
HUMANIZER_MODEL=qwen3:8b
RESEARCH_MODEL=deepseek
INSIGHT_MODEL=deepseek
CRITIC_MODEL=deepseek
PREDICTOR_MODEL=deepseek
DEEPSEEK_MODEL=deepseek-r1:7b
```

Family wins over stale env model names (a reasoning stage will not keep a Qwen model id).

## Future models

Add a provider adapter + map it in `CAPABILITY_FAMILY_PREFERENCE` / family builder. Agents stay unchanged.
