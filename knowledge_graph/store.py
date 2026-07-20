"""Local-first knowledge graph store (JSON)."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from knowledge_graph.schema import GraphEdge, GraphNode, NodeType, RelationType
from shared.knowledge import ROOT

DEFAULT_PATH = ROOT / "knowledge_graph" / "graph.json"


def _slug(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", (text or "").strip().lower()).strip("-") or "node"


class KnowledgeGraph:
    def __init__(self, path: Path | None = None) -> None:
        self.path = path or DEFAULT_PATH
        self.path.parent.mkdir(parents=True, exist_ok=True)
        if not self.path.exists():
            self._write({"nodes": [], "edges": []})

    def _read(self) -> dict[str, Any]:
        with self.path.open(encoding="utf-8") as handle:
            data = json.load(handle)
        if not isinstance(data, dict):
            return {"nodes": [], "edges": []}
        data.setdefault("nodes", [])
        data.setdefault("edges", [])
        return data

    def _write(self, data: dict[str, Any]) -> None:
        with self.path.open("w", encoding="utf-8") as handle:
            json.dump(data, handle, indent=2, ensure_ascii=False)
            handle.write("\n")

    def upsert_node(self, node_type: NodeType | str, label: str, **properties: Any) -> GraphNode:
        ntype = NodeType(node_type) if isinstance(node_type, str) else node_type
        node_id = properties.pop("id", None) or f"{ntype.value.lower()}:{_slug(label)}"
        node = GraphNode(id=node_id, type=ntype, label=label, properties=properties)
        data = self._read()
        for idx, existing in enumerate(data["nodes"]):
            if existing.get("id") == node.id:
                data["nodes"][idx] = node.model_dump()
                self._write(data)
                return node
        data["nodes"].append(node.model_dump())
        self._write(data)
        return node

    def add_edge(
        self,
        source: str,
        target: str,
        relation: RelationType | str,
        **properties: Any,
    ) -> GraphEdge:
        rel = RelationType(relation) if isinstance(relation, str) else relation
        edge_id = properties.pop("id", None) or f"{_slug(source)}:{rel.value}:{_slug(target)}"
        edge = GraphEdge(
            id=edge_id,
            source=source,
            target=target,
            relation=rel,
            properties=properties,
        )
        data = self._read()
        for idx, existing in enumerate(data["edges"]):
            if existing.get("id") == edge.id:
                data["edges"][idx] = edge.model_dump()
                self._write(data)
                return edge
        data["edges"].append(edge.model_dump())
        self._write(data)
        return edge

    def nodes(self) -> list[dict[str, Any]]:
        return list(self._read().get("nodes") or [])

    def edges(self) -> list[dict[str, Any]]:
        return list(self._read().get("edges") or [])

    def relationships_for(self, node_id: str) -> list[dict[str, Any]]:
        return [
            e
            for e in self.edges()
            if e.get("source") == node_id or e.get("target") == node_id
        ]

    def link_topic_to_sources(self, topic: str, source_labels: list[str]) -> None:
        topic_node = self.upsert_node(NodeType.TOPIC, topic)
        for label in source_labels:
            tool = self.upsert_node(NodeType.CONCEPT, label)
            self.add_edge(topic_node.id, tool.id, RelationType.SUPPORTS)
