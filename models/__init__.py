from models.base import ChatMessage, GenerateResult, ModelProvider, ProviderHealth
from models.fake import FakeProvider
from models.ollama import OllamaProvider

__all__ = [
    "ChatMessage",
    "FakeProvider",
    "GenerateResult",
    "ModelProvider",
    "OllamaProvider",
    "ProviderHealth",
]


def __getattr__(name: str):
    # Lazy exports to avoid import cycles with apps.api.config.
    if name == "DeepSeekProvider":
        from models.deepseek_provider import DeepSeekProvider

        return DeepSeekProvider
    if name in {"family_for_stage", "provider_for_stage", "resolve_model_name"}:
        from models import router as _router

        return getattr(_router, name)
    if name in {"Capability", "CAPABILITY_FAMILY_PREFERENCE", "STAGE_CAPABILITIES"}:
        from models import capabilities as _capabilities

        return getattr(_capabilities, name)
    if name in {"ModelOrchestrator", "ProviderSelection"}:
        from models import orchestrator as _orchestrator

        return getattr(_orchestrator, name)
    raise AttributeError(f"module 'models' has no attribute {name!r}")
