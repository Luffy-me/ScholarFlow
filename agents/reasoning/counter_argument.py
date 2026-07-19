"""Challenge every conclusion with reasons it may be wrong."""

from __future__ import annotations

from typing import Any

from agents.reasoning._util import claim_ref, normalize_text, top_claims
from agents.reasoning.schemas import CounterArgument


class CounterArgumentEngine:
    name = "counter_argument"

    def challenge(
        self,
        conclusions: list[str],
        claims: list[dict[str, Any]],
        *,
        hypotheses: list[Any] | None = None,
    ) -> list[CounterArgument]:
        top = top_claims(claims, limit=6)
        refs = [claim_ref(c, i) for i, c in enumerate(top)]
        contradicting = [
            normalize_text(str(c.get("claim")))
            for c in claims
            if c.get("contradicting_sources")
        ]
        low_conf = [
            normalize_text(str(c.get("claim")))
            for c in claims
            if float(c.get("confidence") or 0) < 0.5
        ]
        unverified = [
            normalize_text(str(c.get("claim")))
            for c in claims
            if not c.get("verified")
        ]

        targets = [normalize_text(c) for c in conclusions if normalize_text(c)]
        if not targets and top:
            targets = [normalize_text(str(top[0].get("claim")))]
        if not targets:
            targets = ["No solid conclusion available"]

        alt_from_hyp = []
        for h in hypotheses or []:
            stmt = getattr(h, "statement", None) or (h.get("statement") if isinstance(h, dict) else "")
            if stmt:
                alt_from_hyp.append(normalize_text(str(stmt)))

        out: list[CounterArgument] = []
        for target in targets[:5]:
            reasons = [
                "Evidence Graph may be incomplete for this conclusion.",
                "Observed correlation is not established as causation.",
            ]
            if low_conf:
                reasons.append(f"Low-confidence claim weakens the case: {low_conf[0]}")
            if contradicting:
                reasons.append(f"Contradicting sources exist: {contradicting[0]}")
            if unverified:
                reasons.append(f"Key supporting claim is unverified: {unverified[0]}")

            missing = [
                "Direct causal measurements tied to the conclusion",
                "Disconfirming cases from opposing segments",
            ]
            if not claims:
                missing.append("Any Evidence Graph claim at all")

            alternatives = alt_from_hyp[:3] or [
                "Selection bias in available sources explains the pattern.",
                "Temporary noise is being mistaken for a structural shift.",
            ]
            out.append(
                CounterArgument(
                    target_conclusion=target,
                    reasons_it_may_be_wrong=reasons,
                    missing_evidence=missing,
                    alternative_explanations=alternatives,
                    evidence_refs=refs,
                )
            )
        return out
