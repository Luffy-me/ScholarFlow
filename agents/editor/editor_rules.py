"""Editorial rules — Economist / HBR / Stripe / Linear / Anthropic standards."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class EditorRule:
    code: str
    category: str
    description: str
    why: str


EDITOR_RULES: tuple[EditorRule, ...] = (
    EditorRule(
        "STORY_ARC",
        "story",
        "Post should move context → tension → insight → implication.",
        "Without arc, readers cannot follow the argument.",
    ),
    EditorRule(
        "LOGIC_LINKS",
        "flow",
        "Claims must connect with causal or contrastive glue.",
        "Broken logic destroys trust faster than weak prose.",
    ),
    EditorRule(
        "EVIDENCE_REQUIRED",
        "credibility",
        "Non-trivial claims need Evidence Graph support or clear attribution.",
        "Unsupported assertions read as invention.",
    ),
    EditorRule(
        "NO_FAKE_EXPERIENCE",
        "credibility",
        "Personal/scale claims must exist in verified memory.",
        "Fabricated experience is an integrity failure.",
    ),
    EditorRule(
        "NO_INVENTED_STATS",
        "credibility",
        "Statistics require sources; otherwise reject or attribute.",
        "Invented numbers are never acceptable.",
    ),
    EditorRule(
        "ORIGINALITY",
        "originality",
        "Avoid generic AI / corporate filler.",
        "Commodity language signals low editorial standards.",
    ),
    EditorRule(
        "HUMAN_VOICE",
        "tone",
        "Prefer concrete operator voice over brochure tone.",
        "Authenticity is a trust proxy on LinkedIn.",
    ),
    EditorRule(
        "NO_REPETITION",
        "redundancy",
        "Do not repeat the same phrase or point without new information.",
        "Repetition creates reading fatigue and looks unedited.",
    ),
    EditorRule(
        "SENTENCE_RHYTHM",
        "clarity",
        "Vary sentence length; avoid marathon clauses.",
        "Rhythm controls attention and comprehension.",
    ),
    EditorRule(
        "PARAGRAPH_RHYTHM",
        "clarity",
        "Keep paragraphs short enough to scan on mobile.",
        "Dense walls of text fail LinkedIn friendliness.",
    ),
    EditorRule(
        "TRANSITIONS",
        "flow",
        "Use purposeful transitions; avoid empty connective tissue.",
        "Weak transitions hide structural gaps.",
    ),
    EditorRule(
        "TERMINOLOGY",
        "consistency",
        "Use one term per concept throughout.",
        "Terminology drift looks careless and confuses experts.",
    ),
    EditorRule(
        "TONE_CONSISTENCY",
        "consistency",
        "Keep tone stable for one audience.",
        "Tone shifts break the editorial contract with the reader.",
    ),
    EditorRule(
        "TENSE_CONSISTENCY",
        "consistency",
        "Do not thrash between unrelated tenses without reason.",
        "Tense chaos undermines narrative control.",
    ),
    EditorRule(
        "WEAK_OPENING",
        "copy",
        "Openings must earn the next line.",
        "A weak open wastes the only guaranteed attention.",
    ),
    EditorRule(
        "WEAK_ENDING",
        "copy",
        "Endings should land a decision, question, or implication.",
        "Soft endings dissipate authority.",
    ),
    EditorRule(
        "PASSIVE_VOICE",
        "copy",
        "Prefer active verbs for accountability.",
        "Passive constructions obscure who did what.",
    ),
    EditorRule(
        "PRACTICAL_USE",
        "practicality",
        "Reader should leave with a usable distinction or next step.",
        "Insight without usefulness is commentary, not counsel.",
    ),
    EditorRule(
        "LINKEDIN_SCAN",
        "linkedin",
        "Formatting and length must survive mobile feed scanning.",
        "LinkedIn is a skimming surface first.",
    ),
    EditorRule(
        "EXPLAIN_WHY",
        "process",
        "Every editorial recommendation must state why.",
        "Unexplained edits train authors to ignore the desk.",
    ),
)


def rules_by_category() -> dict[str, list[EditorRule]]:
    out: dict[str, list[EditorRule]] = {}
    for rule in EDITOR_RULES:
        out.setdefault(rule.category, []).append(rule)
    return out


def rule_map() -> dict[str, EditorRule]:
    return {r.code: r for r in EDITOR_RULES}
