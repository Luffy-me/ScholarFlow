"""Reusable carousel components — data only, no rendering."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class Component(BaseModel):
    type: str
    content: str = ""
    props: dict[str, Any] = Field(default_factory=dict)

    def as_element_payload(self) -> dict[str, Any]:
        return {"type": self.type, "content": self.content, **self.props}


def Heading(content: str, level: int = 1, **props: Any) -> Component:
    return Component(type="heading", content=content, props={"level": level, **props})


def Paragraph(content: str, **props: Any) -> Component:
    return Component(type="text", content=content, props=props)


def BulletList(items: list[str], **props: Any) -> Component:
    return Component(type="bullet_list", content="\n".join(items), props={"items": items, **props})


def Callout(content: str, variant: str = "info", **props: Any) -> Component:
    return Component(type="callout", content=content, props={"variant": variant, **props})


def Card(content: str, title: str = "", **props: Any) -> Component:
    return Component(type="card", content=content, props={"title": title, **props})


def Metric(label: str, value: str, **props: Any) -> Component:
    return Component(type="metric", content=value, props={"label": label, **props})


def Table(headers: list[str], rows: list[list[str]], **props: Any) -> Component:
    return Component(type="table", content="", props={"headers": headers, "rows": rows, **props})


def Icon(icon_id: str, **props: Any) -> Component:
    return Component(type="icon", content=icon_id, props={"icon_id": icon_id, **props})


def Divider(**props: Any) -> Component:
    return Component(type="divider", content="", props=props)


def ImagePlaceholder(label: str = "image", **props: Any) -> Component:
    return Component(type="image", content=label, props={"placeholder": True, **props})


def DiagramPlaceholder(mermaid: str = "", kind: str = "Flowchart", **props: Any) -> Component:
    return Component(type="diagram", content=mermaid, props={"kind": kind, "placeholder": False, **props})


def Footer(content: str, **props: Any) -> Component:
    return Component(type="footer", content=content, props=props)


def ProgressIndicator(current: int, total: int, **props: Any) -> Component:
    return Component(
        type="progress",
        content=f"{current}/{total}",
        props={"current": current, "total": total, **props},
    )


COMPONENT_TYPES = [
    "Heading",
    "Paragraph",
    "BulletList",
    "Callout",
    "Card",
    "Metric",
    "Table",
    "Icon",
    "Divider",
    "ImagePlaceholder",
    "DiagramPlaceholder",
    "Footer",
    "ProgressIndicator",
]
