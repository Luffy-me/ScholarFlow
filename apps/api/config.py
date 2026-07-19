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
    writer_model: str = Field(
        default="qwen3:8b",
        validation_alias=AliasChoices("WRITER_MODEL", "writer_model"),
    )
    critic_model: str = Field(
        default="qwen3:4b",
        validation_alias=AliasChoices("CRITIC_MODEL", "critic_model"),
    )
    predictor_model: str = Field(
        default="qwen3:4b",
        validation_alias=AliasChoices("PREDICTOR_MODEL", "predictor_model"),
    )
    humanizer_model: str = Field(
        default="",
        validation_alias=AliasChoices("HUMANIZER_MODEL", "humanizer_model"),
    )
    angle_model: str = Field(
        default="",
        validation_alias=AliasChoices("ANGLE_MODEL", "angle_model"),
    )
    strategist_model: str = Field(
        default="",
        validation_alias=AliasChoices("STRATEGIST_MODEL", "strategist_model"),
    )
    researcher_model: str = Field(
        default="",
        validation_alias=AliasChoices("RESEARCHER_MODEL", "researcher_model"),
    )
    writing_quality_model: str = Field(
        default="",
        validation_alias=AliasChoices("WRITING_QUALITY_MODEL", "writing_quality_model"),
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

    def model_for_stage(self, stage: str) -> str:
        """Resolve per-stage model, falling back to OLLAMA_MODEL."""
        mapping = {
            "writer": self.writer_model or self.ollama_model,
            "humanizer": self.humanizer_model or self.writer_model or self.ollama_model,
            "critic": self.critic_model or self.ollama_model,
            "engagement_predictor": self.predictor_model or self.ollama_model,
            "predictor": self.predictor_model or self.ollama_model,
            "angle_finder": self.angle_model or self.writer_model or self.ollama_model,
            "strategist": self.strategist_model or self.writer_model or self.ollama_model,
            "researcher": self.researcher_model or self.critic_model or self.ollama_model,
            "writing_quality": self.writing_quality_model
            or self.critic_model
            or self.ollama_model,
            "trend_analyzer": self.researcher_model or self.critic_model or self.ollama_model,
            "insight_engine": self.writer_model or self.ollama_model,
        }
        return mapping.get(stage, self.ollama_model)


settings = Settings()
