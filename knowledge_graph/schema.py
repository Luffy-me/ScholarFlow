"""Knowledge graph node/edge vocabulary."""

from __future__ import annotations

from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class NodeType(str, Enum):
    TOPIC = "Topic"
    TOOL = "Tool"
    COMPANY = "Company"
    TECHNOLOGY = "Technology"
    RESEARCH_PAPER = "ResearchPaper"
    PERSON = "Person"
    CONCEPT = "Concept"


class RelationType(str, Enum):
    SUPPORTS = "supports"
    CONTRADICTS = "contradicts"
    DEPENDS_ON = "depends_on"
    COMPARES_TO = "compares_to"
    EXTENDS = "extends"
    SUPERSEDES = "supersedes"


class GraphNode(BaseModel):
    id: str
    type: NodeType
    label: str
    properties: dict[str, Any] = Field(default_factory=dict)


class GraphEdge(BaseModel):
    id: str
    source: str
    target: str
    relation: RelationType
    properties: dict[str, Any] = Field(default_factory=dict)
