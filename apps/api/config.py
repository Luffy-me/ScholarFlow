"""Application settings."""

from __future__ import annotations

from pydantic import AliasChoices, Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    database_url: str = "sqlite+pysqlite:///./linkedin_content.db"
    ollama_base_url: str = Field(
        default="http://localhost:11434",
        validation_alias=AliasChoices("OLLAMA_BASE_URL", "ollama_base_url"),
    )
    # Prefer OLLAMA_MODEL; DEFAULT_MODEL kept for backward compatibility.
    ollama_model: str = Field(
        default="qwen3:8b",
        validation_alias=AliasChoices("OLLAMA_MODEL", "DEFAULT_MODEL", "ollama_model", "default_model"),
    )
    ollama_think: bool = Field(
        default=False,
        validation_alias=AliasChoices("OLLAMA_THINK", "ollama_think"),
    )
    ollama_num_ctx: int = Field(
        default=4096,
        validation_alias=AliasChoices("OLLAMA_NUM_CTX", "ollama_num_ctx"),
    )
    user_memory_path: str = "knowledge/user_memory.json"
    content_modes_path: str = "knowledge/content_modes.json"
    engagement_feedback_path: str = "feedback/engagement_feedback.json"
    research_sources_dir: str = "research_sources"
    use_fake_provider: bool = False

    @property
    def default_model(self) -> str:
        """Alias used across the API and providers."""
        return self.ollama_model


settings = Settings()
