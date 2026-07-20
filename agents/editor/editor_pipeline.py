"""Editorial pipeline — final quality gate before export (critique only)."""

from __future__ import annotations

from typing import Any

from agents.editor.editor import Editor
from agents.editor.schemas import (
    EditorialResult,
    EditorInput,
    EditorOutput,
    PublishDecision,
)


class EditorPipeline:
    """
    Final gate before export:

    ... → LinkedIn Optimizer → EDITORIAL REVIEW → Export

    The editor never writes and never replaces Writer / Research /
    Reasoning / LinkedIn optimizer agents.
    """

    name = "editor_pipeline"
    writes = False

    def __init__(self) -> None:
        self.editor = Editor()

    def review(
        self,
        draft: str,
        *,
        evidence_refs: list[str] | None = None,
        user_memory: dict[str, Any] | None = None,
    ) -> EditorialResult:
        result = self.editor.review(
            draft,
            evidence_refs=evidence_refs,
            user_memory=user_memory,
        )
        result.meta = {
            **result.meta,
            "pipeline_stage": "editorial_review",
            "before_export": True,
            "writes": False,
        }
        return result

    async def run(self, payload: EditorInput | dict[str, Any]) -> EditorOutput:
        if isinstance(payload, dict):
            text = str(payload.get("text") or "")
            extra = payload
            memory = payload.get("user_memory") or {}
            topic = str(payload.get("topic") or "")
        else:
            text = payload.text
            extra = payload.extra or {}
            memory = payload.user_memory or {}
            topic = payload.topic

        result = self.review(
            text,
            evidence_refs=list(extra.get("evidence_refs") or []),
            user_memory=memory if isinstance(memory, dict) else {},
        )
        lines = [
            "Editorial Review",
            f"Topic: {topic or '(from draft)'}",
            f"Decision: {result.publish_decision.value}",
            f"Overall: {result.editorial_report.scores.overall}",
            f"Issues: {len(result.issues)}",
        ]
        if result.publish_decision == PublishDecision.APPROVE:
            lines.append("Approved draft ready for export.")
        else:
            lines.append("Draft not approved — see issues/suggestions (no rewrite applied).")

        return EditorOutput(
            text="\n".join(lines),
            result=result,
            data=result.as_dict(),
            meta={"agent": self.name, "writes": False, "rewrites": False},
        )


EditorialReviewEngine = EditorPipeline
