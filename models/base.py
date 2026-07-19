"""Model provider interface and shared types."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Literal


Role = Literal["system", "user", "assistant"]


@dataclass
class ChatMessage:
    role: Role
    content: str


@dataclass
class GenerateResult:
    text: str
    model: str
    provider: str
    raw: dict[str, Any] = field(default_factory=dict)


@dataclass
class ProviderHealth:
    online: bool
    provider: str
    models: list[str] = field(default_factory=list)
    detail: str = ""


class ModelProvider(ABC):
    """Agents depend on this interface — never on a vendor SDK directly."""

    name: str

    @abstractmethod
    async def health(self) -> ProviderHealth:
        raise NotImplementedError

    @abstractmethod
    async def generate(
        self,
        messages: list[ChatMessage],
        *,
        model: str | None = None,
        temperature: float = 0.4,
        response_format: str | None = None,
    ) -> GenerateResult:
        raise NotImplementedError
