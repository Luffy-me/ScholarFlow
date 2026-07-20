"""Shared agent contracts."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Generic, TypeVar

from pydantic import BaseModel, Field

from models.base import ModelProvider


class AgentInput(BaseModel):
    topic: str = ""
    content_mode: str = "founder"
    format: str = "short"
    text: str = ""
    user_memory: dict[str, Any] = Field(default_factory=dict)
    extra: dict[str, Any] = Field(default_factory=dict)


class AgentOutput(BaseModel):
    text: str = ""
    data: dict[str, Any] = Field(default_factory=dict)
    meta: dict[str, Any] = Field(default_factory=dict)


InputT = TypeVar("InputT", bound=AgentInput)
OutputT = TypeVar("OutputT", bound=AgentOutput)


class Agent(ABC, Generic[InputT, OutputT]):
    name: str

    def __init__(self, provider: ModelProvider) -> None:
        self.provider = provider

    @abstractmethod
    async def run(self, payload: InputT) -> OutputT:
        raise NotImplementedError
