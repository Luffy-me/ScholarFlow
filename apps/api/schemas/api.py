from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class GenerateRequest(BaseModel):
    topic: str
    content_mode: str = "founder"
    format: str = "short"
    audience: str = ""
    selected_angle_index: int = 0
    save: bool = True


class ExperiencePropose(BaseModel):
    statement: str
    category: str = "other"
    tags: list[str] = Field(default_factory=list)
    related_projects: list[str] = Field(default_factory=list)
    persist: bool = True


class ExperienceDecision(BaseModel):
    experience_id: str
    persist: bool = True


class EvidenceCreate(BaseModel):
    source: str
    date: str | None = None
    confidence: float | None = Field(default=None, ge=0, le=1)
    extracted_claim: str
    url: str | None = None
    title: str | None = None


class EngagementFeedbackCreate(BaseModel):
    impressions: int = 0
    likes: int = 0
    comments: int = 0
    reposts: int = 0
    saves: int = 0
    user_rating: int | None = Field(default=None, ge=1, le=5)
    notes: str | None = None


class PostUpdate(BaseModel):
    body: str | None = None
    status: str | None = None
    title: str | None = None
    tags: list[str] | None = None


class MemoryUpdate(BaseModel):
    memory: dict[str, Any]
