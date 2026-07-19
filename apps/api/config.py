"""Application settings."""

from __future__ import annotations

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    database_url: str = "sqlite+pysqlite:///./linkedin_content.db"
    ollama_base_url: str = "http://localhost:11434"
    default_model: str = "qwen2.5:7b"
    user_memory_path: str = "knowledge/user_memory.json"
    content_modes_path: str = "knowledge/content_modes.json"
    engagement_feedback_path: str = "feedback/engagement_feedback.json"
    research_sources_dir: str = "research_sources"
    use_fake_provider: bool = False


settings = Settings()
