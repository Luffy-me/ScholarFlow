"""Diagram Engine — structured diagram specs + Mermaid generation."""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field

DiagramKind = Literal[
    "Architecture",
    "Flowchart",
    "Sequence",
    "Timeline",
    "Mindmap",
    "Roadmap",
    "Decision Tree",
    "Comparison",
    "Matrix",
    "Cycle",
]


class DiagramSpec(BaseModel):
    kind: str
    title: str = ""
    nodes: list[str] = Field(default_factory=list)
    edges: list[list[str]] = Field(default_factory=list)
    mermaid: str = ""
    meta: dict[str, Any] = Field(default_factory=dict)


class DiagramEngine:
    name = "diagram_engine"

    def build(
        self,
        kind: str,
        *,
        title: str,
        labels: list[str] | None = None,
    ) -> DiagramSpec:
        labels = labels or ["Input", "Process", "Output"]
        nodes = [str(x) for x in labels if str(x).strip()][:8] or ["A", "B", "C"]
        edges: list[list[str]] = []
        if kind in {"Flowchart", "Sequence", "Timeline", "Roadmap", "Cycle"}:
            for i in range(len(nodes) - 1):
                edges.append([nodes[i], nodes[i + 1]])
            if kind == "Cycle" and len(nodes) > 1:
                edges.append([nodes[-1], nodes[0]])
        elif kind in {"Architecture", "Mindmap"}:
            hub = nodes[0]
            for n in nodes[1:]:
                edges.append([hub, n])
        elif kind == "Decision Tree":
            if len(nodes) >= 3:
                edges = [[nodes[0], nodes[1]], [nodes[0], nodes[2]]]
            else:
                edges = [[nodes[0], nodes[-1]]]
        elif kind == "Comparison":
            edges = []
        elif kind == "Matrix":
            edges = []
        else:
            for i in range(len(nodes) - 1):
                edges.append([nodes[i], nodes[i + 1]])

        mermaid = self.to_mermaid(kind, title=title, nodes=nodes, edges=edges)
        return DiagramSpec(kind=kind, title=title, nodes=nodes, edges=edges, mermaid=mermaid)

    def to_mermaid(
        self,
        kind: str,
        *,
        title: str,
        nodes: list[str],
        edges: list[list[str]],
    ) -> str:
        def nid(label: str, idx: int) -> str:
            return f"n{idx}"

        index = {label: nid(label, i) for i, label in enumerate(nodes)}
        lines = [f"%% {title}"]
        if kind == "Mindmap":
            lines.append("mindmap")
            lines.append(f"  root(({nodes[0]}))" if nodes else "  root((Topic))")
            for n in nodes[1:]:
                lines.append(f"    {n}")
            return "\n".join(lines)
        if kind == "Sequence":
            lines.append("sequenceDiagram")
            for a, b in edges:
                lines.append(f"  {index[a]}->>{index[b]}: next")
            for label, i in index.items():
                lines.insert(1, f"  participant {i} as {label}")
            return "\n".join(lines)
        # default flowchart
        lines.append("flowchart TD")
        for label, i in index.items():
            safe = label.replace('"', "'")
            lines.append(f'  {i}["{safe}"]')
        for a, b in edges:
            lines.append(f"  {index[a]} --> {index[b]}")
        return "\n".join(lines)
