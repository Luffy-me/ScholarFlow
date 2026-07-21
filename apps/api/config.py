"""Application settings."""

from __future__ import annotations

from pydantic import AliasChoices, Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

from apps.api import ai_config


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    database_url: str = "sqlite+pysqlite:///./linkedin_content.db"
    ollama_base_url: str = Field(
        default=ai_config.OLLAMA_BASE_URL,
        validation_alias=AliasChoices("OLLAMA_BASE_URL", "ollama_base_url"),
    )
    ollama_model: str = Field(
        default=ai_config.OLLAMA_MODEL,
        validation_alias=AliasChoices("OLLAMA_MODEL", "DEFAULT_MODEL", "ollama_model", "default_model"),
    )

    writer_model: str = Field(
        default=ai_config.WRITER_MODEL,
        validation_alias=AliasChoices("WRITER_MODEL", "writer_model"),
    )
    humanizer_model: str = Field(
        default=ai_config.HUMANIZER_MODEL,
        validation_alias=AliasChoices("HUMANIZER_MODEL", "humanizer_model"),
    )

    research_model: str = Field(
        default=ai_config.DEEPSEEK_MODEL,
        validation_alias=AliasChoices("RESEARCH_MODEL", "RESEARCHER_MODEL", "research_model", "researcher_model"),
    )
    insight_model: str = Field(
        default=ai_config.DEEPSEEK_MODEL,
        validation_alias=AliasChoices("INSIGHT_MODEL", "insight_model"),
    )
    critic_model: str = Field(
        default=ai_config.CRITIC_MODEL,
        validation_alias=AliasChoices("CRITIC_MODEL", "critic_model"),
    )
    predictor_model: str = Field(
        default=ai_config.PREDICTOR_MODEL,
        validation_alias=AliasChoices("PREDICTOR_MODEL", "predictor_model"),
    )
    deepseek_model: str = Field(
        default=ai_config.DEEPSEEK_MODEL,
        validation_alias=AliasChoices("DEEPSEEK_MODEL", "deepseek_model"),
    )

    angle_model: str = Field(
        default="",
        validation_alias=AliasChoices("ANGLE_MODEL", "angle_model"),
    )
    strategist_model: str = Field(
        default="",
        validation_alias=AliasChoices("STRATEGIST_MODEL", "strategist_model"),
    )
    writing_quality_model: str = Field(
        default="",
        validation_alias=AliasChoices("WRITING_QUALITY_MODEL", "writing_quality_model"),
    )
    trend_model: str = Field(
        default="",
        validation_alias=AliasChoices("TREND_MODEL", "trend_model"),
    )

    ollama_think: bool = Field(
        default=ai_config.OLLAMA_THINK,
        validation_alias=AliasChoices("OLLAMA_THINK", "ollama_think"),
    )
    ollama_num_ctx: int = Field(
        default=ai_config.OLLAMA_NUM_CTX,
        validation_alias=AliasChoices("OLLAMA_NUM_CTX", "ollama_num_ctx"),
    )
    ollama_connect_timeout: float = Field(
        default=ai_config.OLLAMA_CONNECT_TIMEOUT,
        validation_alias=AliasChoices("OLLAMA_CONNECT_TIMEOUT", "ollama_connect_timeout"),
    )
    ollama_generation_timeout: float = Field(
        default=ai_config.OLLAMA_GENERATION_TIMEOUT,
        validation_alias=AliasChoices("OLLAMA_GENERATION_TIMEOUT", "ollama_generation_timeout"),
    )
    ollama_max_retries: int = Field(
        default=ai_config.OLLAMA_MAX_RETRIES,
        validation_alias=AliasChoices("OLLAMA_MAX_RETRIES", "ollama_max_retries"),
    )
    api_port: int = Field(
        default=ai_config.API_PORT,
        validation_alias=AliasChoices("API_PORT", "api_port"),
    )
    frontend_port: int = Field(
        default=ai_config.FRONTEND_PORT,
        validation_alias=AliasChoices("FRONTEND_PORT", "frontend_port"),
    )
    debate_mode: bool = Field(
        default=True,
        validation_alias=AliasChoices("DEBATE_MODE", "debate_mode"),
    )
    user_memory_path: str = "knowledge/user_memory.json"
    content_modes_path: str = "knowledge/content_modes.json"
    engagement_feedback_path: str = "feedback/engagement_feedback.json"
    research_sources_dir: str = "research_sources"
    use_fake_provider: bool = False

    @field_validator("ollama_base_url", mode="before")
    @classmethod
    def _normalize_ollama_url(cls, value: object) -> object:
        if not isinstance(value, str):
            return value
        trimmed = value.strip().rstrip("/")
        if trimmed.startswith("http://localhost:"):
            return "http://127.0.0.1" + trimmed[len("http://localhost") :]
        if trimmed.startswith("https://localhost:"):
            return "https://127.0.0.1" + trimmed[len("https://localhost") :]
        return trimmed

    @property
    def default_model(self) -> str:
        return self.ollama_model

    def resolved_deepseek_model(self) -> str:
        candidate = (self.deepseek_model or ai_config.DEEPSEEK_MODEL).strip()
        if candidate.lower() in {"deepseek", "deepseek-r1"}:
            return ai_config.DEEPSEEK_MODEL
        return candidate

    def _expand(self, value: str, *, writing: bool = False) -> str:
        raw = (value or "").strip()
        if not raw:
            return self.writer_model if writing else self.resolved_deepseek_model()
        if raw.lower() in {"deepseek", "deepseek-r1"}:
            return self.resolved_deepseek_model()
        if raw.lower() in {"qwen", "qwen3"}:
            return self.writer_model or self.ollama_model
        return raw

    def model_for_stage(self, stage: str) -> str:
        key = (stage or "").strip().lower()
        deepseek = self.resolved_deepseek_model()
        qwen = self._expand(self.writer_model, writing=True)

        mapping = {
            "writer": self._expand(self.writer_model, writing=True),
            "humanizer": self._expand(self.humanizer_model or self.writer_model, writing=True),
            "debate_rewrite": self._expand(self.writer_model, writing=True),
            "researcher": self._expand(self.research_model),
            "research_agent": self._expand(self.research_model),
            "research": self._expand(self.research_model),
            "trend_analyzer": self._expand(self.trend_model or self.research_model),
            "trend_analysis": self._expand(self.trend_model or self.research_model),
            "insight_engine": self._expand(self.insight_model),
            "insight": self._expand(self.insight_model),
            "claim_checker": deepseek,
            "grounding": deepseek,
            "critic": self._expand(self.critic_model),
            "debate_critic": self._expand(self.critic_model),
            "debate_final": self._expand(self.critic_model),
            "engagement_predictor": self._expand(self.predictor_model),
            "predictor": self._expand(self.predictor_model),
            "writing_quality": self._expand(self.writing_quality_model or self.critic_model),
            "angle_finder": self._expand(self.angle_model or self.insight_model),
            "strategist": self._expand(self.strategist_model or self.insight_model),
        }
        return mapping.get(key, deepseek if key else qwen)


settings = Settings()
