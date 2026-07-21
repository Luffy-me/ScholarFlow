"""Central AI / Ollama configuration defaults.

All runtime defaults for local models live here. `apps.api.config.Settings`
reads these values; agents resolve models via `settings.model_for_stage()`.
"""

from __future__ import annotations

OLLAMA_BASE_URL = "http://127.0.0.1:11434"
OLLAMA_MODEL = "qwen3:8b"
WRITER_MODEL = "qwen3:8b"
HUMANIZER_MODEL = "qwen3:8b"
CRITIC_MODEL = "deepseek-r1:8b"
PREDICTOR_MODEL = "deepseek-r1:8b"
DEEPSEEK_MODEL = "deepseek-r1:8b"
OLLAMA_THINK = False
OLLAMA_NUM_CTX = 4096
OLLAMA_CONNECT_TIMEOUT = 5.0
OLLAMA_GENERATION_TIMEOUT = 300.0
OLLAMA_MAX_RETRIES = 2

API_PORT = 8000
FRONTEND_PORT = 3000

# Stages that must be present in Ollama for full pipeline (startup warnings).
REQUIRED_OLLAMA_MODELS = (
    WRITER_MODEL,
    CRITIC_MODEL,
    PREDICTOR_MODEL,
)
