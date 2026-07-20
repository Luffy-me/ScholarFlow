"""Hook optimizer — evaluate opening + generate 5 ranked alternatives (no new facts)."""

from __future__ import annotations

import re

from agents.linkedin_optimizer._text import (
    clamp01,
    first_sentence,
    first_two_lines,
    has_number,
    has_question,
    has_specific_noun,
    mean,
    normalize,
    words,
)
from agents.linkedin_optimizer.schemas import HookAlternative, HookOptimization, HookScores
from shared.quality import scan_text


class HookOptimizer:
    name = "hook_optimizer"

    def score_hook(self, hook_text: str, *, full_text: str = "") -> HookScores:
        text = normalize(hook_text)
        opening = first_two_lines(text) or text
        scan = scan_text(full_text or text)

        curiosity = 0.35
        if has_question(opening):
            curiosity += 0.25
        if re.search(r"\b(but|however|instead|except|unless)\b", opening, re.I):
            curiosity += 0.15
        if re.search(r"\b(most|everyone|nobody)\b", opening, re.I):
            curiosity += 0.1
        if scan.has_weak_hook:
            curiosity -= 0.25

        specificity = 0.25
        if has_number(opening):
            specificity += 0.3
        if has_specific_noun(opening):
            specificity += 0.2
        if len(words(opening)) >= 8:
            specificity += 0.1

        novelty = 0.3
        if re.search(r"\b(contrary|overlooked|counterintuitive|myth|wrong)\b", opening, re.I):
            novelty += 0.35
        if scan.has_generic_ai:
            novelty -= 0.2

        authority = 0.25
        if re.search(r"\b(I|we|our team|in practice|measured|tested)\b", opening, re.I):
            authority += 0.25
        if has_number(opening):
            authority += 0.15
        if scan.has_fake_experience:
            authority = min(authority, 0.2)

        stop_scroll = mean([curiosity, specificity, novelty]) * 0.85 + 0.15 * authority
        if len(words(opening)) > 40:
            stop_scroll -= 0.15
        if len(words(opening)) < 4:
            stop_scroll -= 0.2

        overall = mean([curiosity, specificity, novelty, authority, stop_scroll])
        return HookScores(
            curiosity=round(clamp01(curiosity), 4),
            specificity=round(clamp01(specificity), 4),
            novelty=round(clamp01(novelty), 4),
            authority=round(clamp01(authority), 4),
            stop_scroll=round(clamp01(stop_scroll), 4),
            overall=round(clamp01(overall), 4),
        )

    def _alternatives_from_body(self, text: str) -> list[str]:
        """Generate hook variants by rearranging existing content — no invented facts."""
        fs = first_sentence(text)
        body_sentences = [s for s in re.split(r"(?<=[.!?])\s+", normalize(text).replace("\n", " ")) if s.strip()]
        concrete = next((s for s in body_sentences[1:] if has_number(s) or has_specific_noun(s)), "")
        contrast = next(
            (s for s in body_sentences if re.search(r"\b(but|however|instead|wrong|myth)\b", s, re.I)),
            "",
        )
        question_seed = words(fs)[:8]
        q = ("What if " + " ".join(question_seed).rstrip(".!?") + "?").strip()
        if len(words(q)) < 4:
            q = "What actually changed — and what didn't?"

        alts = [
            fs,
            (concrete[:180] if concrete else fs),
            (contrast[:180] if contrast else fs),
            q if "?" in q else fs + ("?" if not fs.endswith("?") else ""),
            (f"{fs}\n{concrete}" if concrete and concrete != fs else f"{fs}\nHere's the constraint."),
        ]
        # Deduplicate while preserving order
        seen: set[str] = set()
        unique: list[str] = []
        for alt in alts:
            key = normalize(alt).lower()
            if not key or key in seen:
                # fallback: tighten original first sentence
                alt = fs[:120]
                key = alt.lower()
            if key in seen:
                continue
            seen.add(key)
            unique.append(normalize(alt))
        while len(unique) < 5:
            unique.append(fs[: max(20, 100 - len(unique) * 5)])
        return unique[:5]

    def optimize(self, text: str) -> HookOptimization:
        text = normalize(text)
        two = first_two_lines(text)
        one = first_sentence(text)
        base_scores = self.score_hook(two or one, full_text=text)
        alts_raw = self._alternatives_from_body(text)
        scored: list[HookAlternative] = []
        for alt in alts_raw:
            scores = self.score_hook(alt, full_text=text)
            scored.append(
                HookAlternative(
                    text=alt,
                    scores=scores,
                    rationale="Derived from existing draft content; no new facts added.",
                )
            )
        scored.sort(key=lambda a: (a.scores.overall, a.scores.stop_scroll), reverse=True)
        for i, alt in enumerate(scored, start=1):
            alt.rank = i
        selected = scored[0].text if scored else one
        recs: list[str] = []
        if base_scores.stop_scroll < 0.55:
            recs.append("Opening lacks stop-scroll tension; prefer the top-ranked alternative.")
        if base_scores.specificity < 0.45:
            recs.append("Increase specificity in the first sentence using details already in the draft.")
        if scan_text(text).has_weak_hook:
            recs.append("Weak/generic hook pattern detected — avoid motivational openers.")
        return HookOptimization(
            first_two_lines=two,
            first_sentence=one,
            scores=base_scores,
            alternatives=scored,
            selected=selected,
            recommendations=recs,
        )
