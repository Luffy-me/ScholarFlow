"""Reflection — ask what was overlooked before finalizing thoughts."""

from __future__ import annotations

from typing import Any

from agents.reasoning._util import normalize_text
from agents.reasoning.schemas import ReflectionResult, ThoughtInsight


class ReflectionEngine:
    name = "reflection"

    def reflect(
        self,
        topic: str,
        *,
        claims: list[dict[str, Any]],
        insights: list[ThoughtInsight],
        contradictions: list[Any] | None = None,
        counterarguments: list[Any] | None = None,
        open_questions: list[str] | None = None,
    ) -> ReflectionResult:
        topic = normalize_text(topic)
        overlooked: list[str] = []
        questions: list[str] = [
            f"What did we overlook about {topic}?",
        ]
        tightened: list[str] = []

        if not claims:
            overlooked.append("No Evidence Graph claims were available — conclusions must stay provisional.")
        unverified = [c for c in claims if not c.get("verified")]
        if unverified:
            overlooked.append(
                f"{len(unverified)} unverified claim(s) were used as weak support and need attribution."
            )
        if contradictions:
            overlooked.append("Contradictions exist; a single narrative may over-smooth reality.")
        if counterarguments:
            ca0 = counterarguments[0]
            missing = getattr(ca0, "missing_evidence", None) or (
                ca0.get("missing_evidence") if isinstance(ca0, dict) else []
            )
            for m in list(missing)[:2]:
                overlooked.append(f"Missing evidence flagged: {m}")

        for insight in insights:
            if not insight.who_loses:
                overlooked.append(f"Insight lacks losers analysis: {insight.statement[:80]}")
            if not insight.what_is_missing:
                overlooked.append(f"Insight lacks 'what is missing': {insight.statement[:80]}")
            if insight.evidence_refs:
                tightened.append(
                    f"Keep '{insight.statement[:100]}' only with refs {insight.evidence_refs[:2]}"
                )
            else:
                tightened.append(
                    f"Downgrade or drop '{insight.statement[:100]}' — no Evidence Graph refs."
                )

        for q in open_questions or []:
            if normalize_text(q):
                questions.append(normalize_text(q))

        questions.append("Which competing hypothesis would most change the decision if true?")
        questions.append("What measurement would falsify the primary claim fastest?")

        # Deterministic unique preserve order
        def _uniq(items: list[str]) -> list[str]:
            seen: set[str] = set()
            out: list[str] = []
            for item in items:
                key = item.lower()
                if key in seen:
                    continue
                seen.add(key)
                out.append(item)
            return out

        return ReflectionResult(
            overlooked=_uniq(overlooked),
            questions_raised=_uniq(questions),
            tightened_conclusions=_uniq(tightened),
        )
