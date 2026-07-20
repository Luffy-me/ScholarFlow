"""Structure optimizer — rhythm, flow, whitespace, scanning (recommendations + safe edits)."""

from __future__ import annotations

from agents.linkedin_optimizer._text import (
    clamp01,
    ensure_paragraph_breaks,
    mean,
    normalize,
    paragraphs,
    sentences,
    variety_score,
    word_count,
    words,
)
from agents.linkedin_optimizer.schemas import StructureOptimization


class StructureOptimizer:
    name = "structure_optimizer"

    def analyze(self, text: str) -> StructureOptimization:
        text = normalize(text)
        sents = sentences(text)
        paras = paragraphs(text)
        lengths = [len(words(s)) for s in sents] or [0]
        para_lens = [len(words(p)) for p in paras] or [word_count(text)]

        # Paragraph rhythm: prefer short blocks
        avg_para = mean([float(x) for x in para_lens])
        paragraph_rhythm = clamp01(1.15 - abs(avg_para - 40) / 80)

        story_flow = 0.45
        if len(paras) >= 3:
            story_flow += 0.2
        if any(re_search_transition(p) for p in paras):
            story_flow += 0.2
        if len(sents) >= 4:
            story_flow += 0.1

        sentence_variety = variety_score(lengths)
        whitespace = 0.3
        if "\n\n" in text:
            whitespace += 0.4
        if text.count("\n") >= 3:
            whitespace += 0.2
        if avg_para > 90:
            whitespace -= 0.25

        transitions = 0.35 + (0.4 if any(re_search_transition(p) for p in paras) else 0.0)
        if len(paras) >= 2:
            transitions += 0.15

        scanning = mean([paragraph_rhythm, whitespace, sentence_variety])
        overall = mean(
            [paragraph_rhythm, story_flow, sentence_variety, whitespace, transitions, scanning]
        )

        recs: list[str] = []
        if whitespace < 0.55:
            recs.append("Add whitespace: break into shorter paragraph blocks for mobile scanning.")
        if sentence_variety < 0.4:
            recs.append("Vary sentence length; mix a short punch line with a longer explanatory line.")
        if story_flow < 0.55:
            recs.append("Clarify story flow: context → tension → insight → implication.")
        if transitions < 0.5:
            recs.append("Add clearer transitions between beats (However / Instead / What changed).")
        if avg_para > 70:
            recs.append("Reduce paragraph length; aim for 2–4 lines per block.")

        return StructureOptimization(
            paragraph_rhythm=round(clamp01(paragraph_rhythm), 4),
            story_flow=round(clamp01(story_flow), 4),
            sentence_variety=round(clamp01(sentence_variety), 4),
            whitespace=round(clamp01(whitespace), 4),
            transitions=round(clamp01(transitions), 4),
            scanning=round(clamp01(scanning), 4),
            overall=round(clamp01(overall), 4),
            recommendations=recs,
        )

    def apply_safe_structure(self, text: str) -> str:
        """Improve scanning/whitespace without changing wording/facts."""
        return ensure_paragraph_breaks(normalize(text))


def re_search_transition(text: str) -> bool:
    import re

    return bool(
        re.search(
            r"\b(however|instead|but|so|therefore|what changed|next|then|because)\b",
            text or "",
            re.I,
        )
    )
