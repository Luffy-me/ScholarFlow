"""AI Writing Quality Analyzer — pattern risk, not authorship detection."""

from __future__ import annotations

import json
import re
from collections import Counter
from typing import Any

from agents.grounding import check_claims
from agents.writing_quality.prompts import SYSTEM_PROMPT, build_enrichment_user_prompt
from agents.writing_quality.schemas import (
    DetectedPattern,
    WritingQualityInput,
    WritingQualityOutput,
)
from models.base import ChatMessage, ModelProvider
from shared.knowledge import (
    allowed_experience_texts,
    load_ai_writing_guidelines,
    load_user_memory,
)
from shared.quality import clamp_score


_SEVERITY_WEIGHT = {
    "critical": 28,
    "high": 18,
    "medium": 12,
    "low": 6,
}

_FIRST_PERSON_RE = re.compile(r"\b(I|I'm|I've|I'd|me|my|mine|we|we're|we've|our)\b", re.I)
_PERSONAL_OBS_RE = re.compile(
    r"\b(I noticed|While building|The surprising part was|I keep coming back|"
    r"I tested|I learned|I built|I almost|In my experience)\b",
    re.I,
)
_OPINION_RE = re.compile(
    r"\b(I disagree|My view is|I care more|I would rather|I think|My biggest takeaway|"
    r"What I learned|The lesson was)\b",
    re.I,
)
_FORMULAIC_RE = re.compile(
    r"("
    r"\bis not about\b.+\bit(?:'s| is) about\b|"
    r"\bIt'?s not\b.+\bIt'?s\b|"
    r"\bHere are \d+ tips\b|"
    r"\bStep\s+\d+\s*:|"
    r"\bTip\s*#?\s*\d+\b"
    r")",
    re.I | re.S,
)
_HEADING_RE = re.compile(r"(?m)^#{1,6}\s+\S+")
_BULLET_RE = re.compile(r"(?m)^\s*[-*•]\s+\S+")
_NUMBERED_RE = re.compile(r"(?m)^\s*\d+[.)]\s+\S+")
_BOLD_RE = re.compile(r"\*\*[^*]{2,}\*\*")
_URL_RE = re.compile(r"https?://\S+", re.I)
_FAKE_SOURCE_RE = re.compile(
    r"\b("
    r"according to a (recent )?study|"
    r"a harvard study|"
    r"statistics show|"
    r"research proves|"
    r"a new report (shows|found)|"
    r"peer[- ]reviewed study"
    r")\b",
    re.I,
)
_INFLATED_RE = re.compile(
    r"\b("
    r"transformative milestone|"
    r"monumental shift|"
    r"unlock unprecedented|"
    r"redefine the future|"
    r"exponential growth|"
    r"seamless integration"
    r")\b",
    re.I,
)
_CERTAINTY_RE = re.compile(
    r"\b("
    r"will definitely|"
    r"will replace|"
    r"never fails|"
    r"guaranteed to|"
    r"inevitably|"
    r"always\b"
    r")",
    re.I,
)
_SUMMARY_RE = re.compile(
    r"\b(in conclusion|to summarize|as mentioned (above|earlier)|as I said before)\b",
    re.I,
)
_METRIC_SCALE_RE = re.compile(
    r"\b("
    r"\d{1,3}(?:,\d{3})+|"
    r"\d+\s*%|"
    r"\d{4,}\s+(users|customers|clients)|"
    r"helped\s+\d+\s+users|"
    r"million[- ]user"
    r")\b",
    re.I,
)


def _category_map(guidelines: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {str(item["id"]): item for item in guidelines.get("detection_categories", []) if item.get("id")}


def _add_pattern(
    detected: list[DetectedPattern],
    *,
    category: str,
    severity: str,
    example: str,
    explanation: str,
) -> None:
    key = (category, example.lower().strip())
    if any((p.category, p.example.lower().strip()) == key for p in detected):
        return
    detected.append(
        DetectedPattern(
            category=category,
            severity=severity,
            example=example.strip()[:180],
            explanation=explanation,
        )
    )


def _detect_phrase_categories(
    text: str,
    categories: dict[str, dict[str, Any]],
    ids: list[str],
    detected: list[DetectedPattern],
) -> None:
    lower = text.lower()
    for cat_id in ids:
        meta = categories.get(cat_id) or {}
        severity = str(meta.get("severity", "medium"))
        problem = str(meta.get("problem", "Low-quality AI writing pattern"))
        for phrase in meta.get("examples", []):
            if phrase and phrase.lower() in lower:
                _add_pattern(
                    detected,
                    category=cat_id,
                    severity=severity,
                    example=phrase,
                    explanation=problem,
                )


def _detect_repetition(text: str, categories: dict[str, dict[str, Any]], detected: list[DetectedPattern]) -> None:
    meta = categories.get("repetition") or {}
    severity = str(meta.get("severity", "medium"))
    sentences = [s.strip() for s in re.split(r"[.!?\n]+", text) if s.strip()]
    normalized = [re.sub(r"\s+", " ", s.lower()) for s in sentences if len(s.split()) >= 4]
    counts = Counter(normalized)
    for sentence, count in counts.items():
        if count >= 2:
            _add_pattern(
                detected,
                category="repetition",
                severity=severity,
                example=sentence[:160],
                explanation="Repeating the same idea weakens authenticity.",
            )
            break
    if _SUMMARY_RE.search(text):
        match = _SUMMARY_RE.search(text)
        _add_pattern(
            detected,
            category="repetition",
            severity=severity,
            example=match.group(0) if match else "to summarize",
            explanation="Unnecessary summary language often pads AI-like drafts.",
        )


def _detect_formatting(text: str, categories: dict[str, dict[str, Any]], detected: list[DetectedPattern]) -> None:
    meta = categories.get("excessive_formatting") or {}
    severity = str(meta.get("severity", "low"))
    headings = len(_HEADING_RE.findall(text))
    bullets = len(_BULLET_RE.findall(text))
    numbered = len(_NUMBERED_RE.findall(text))
    bolds = len(_BOLD_RE.findall(text))
    if headings >= 3 or bullets >= 6 or numbered >= 5 or bolds >= 4:
        _add_pattern(
            detected,
            category="excessive_formatting",
            severity=severity,
            example=f"headings={headings}, bullets={bullets}, numbered={numbered}, bold={bolds}",
            explanation="Heavy formatting can read as template-generated LinkedIn copy.",
        )


def _detect_formulaic(text: str, categories: dict[str, dict[str, Any]], detected: list[DetectedPattern]) -> None:
    meta = categories.get("formulaic_structure") or {}
    severity = str(meta.get("severity", "medium"))
    match = _FORMULAIC_RE.search(text)
    if match:
        _add_pattern(
            detected,
            category="formulaic_structure",
            severity=severity,
            example=match.group(0)[:160],
            explanation="Predictable templates reduce originality.",
        )
    if len(_NUMBERED_RE.findall(text)) >= 4:
        _add_pattern(
            detected,
            category="formulaic_structure",
            severity=severity,
            example="excessive numbered list",
            explanation="Long tip/list templates are a common low-quality AI structure.",
        )


def _detect_truth_integrated(
    text: str,
    memory: dict[str, Any],
    categories: dict[str, dict[str, Any]],
    detected: list[DetectedPattern],
) -> list[str]:
    """Integrate Truth Layer for fake sources / unverified scale claims."""
    meta = categories.get("fake_sources") or {}
    severity = str(meta.get("severity", "critical"))
    improvements: list[str] = []

    for match in _FAKE_SOURCE_RE.finditer(text):
        _add_pattern(
            detected,
            category="fake_sources",
            severity=severity,
            example=match.group(0),
            explanation="Invented or unspecified research citations are not allowed.",
        )
        improvements.append("Remove unverified study/citation language or attach real evidence.")

    for match in _URL_RE.finditer(text):
        url = match.group(0)
        # Treat obviously placeholder/fake hosts as fake sources.
        if "example" in url.lower() or "fake" in url.lower():
            _add_pattern(
                detected,
                category="fake_sources",
                severity=severity,
                example=url,
                explanation="Placeholder or fake URL detected.",
            )

    claim_result = check_claims(text, memory)
    for claim in claim_result.rejected_claims:
        if claim.claim_type in {"metric", "achievement", "client", "quote"}:
            _add_pattern(
                detected,
                category="fake_sources",
                severity=severity,
                example=claim.text[:160],
                explanation=f"Truth Layer rejected ungrounded {claim.claim_type}: {claim.reason}",
            )
            improvements.append(
                f"Remove or verify the {claim.claim_type} claim before publishing."
            )

    # Explicit productivity-scale claims often miss claim-checker patterns.
    for match in _METRIC_SCALE_RE.finditer(text):
        snippet = match.group(0)
        allowed = {a.lower() for a in allowed_experience_texts(memory)}
        grounded = any(snippet.lower() in item or item in snippet.lower() for item in allowed)
        if not grounded and any(tok in snippet.lower() for tok in ("user", "customer", "%", "million")):
            _add_pattern(
                detected,
                category="fake_sources",
                severity=severity,
                example=snippet,
                explanation="Scale/metric claim is not present in verified memory.",
            )
            improvements.append("Drop unverified user/metric claims unless approved in memory.")

    return improvements


def _preferred_hits(text: str, guidelines: dict[str, Any]) -> list[str]:
    hits: list[str] = []
    lower = text.lower()
    for pattern in guidelines.get("preferred_patterns", []):
        pid = str(pattern.get("id", ""))
        examples = pattern.get("examples", [])
        # Prefer literal phrase examples over conceptual labels.
        literal_examples = [
            e
            for e in examples
            if isinstance(e, str)
            and (e.startswith("I") or e[:1].isupper() or " " in e)
            and e.lower()
            not in {
                "tools used",
                "experiments",
                "failures",
                "verified numbers only",
                "named tools",
                "named projects",
                "one failure mode",
                "one workflow step",
            }
        ]
        if any(e.lower() in lower for e in literal_examples):
            hits.append(pid)
    if _PERSONAL_OBS_RE.search(text) and "personal_observation" not in hits:
        hits.append("personal_observation")
    if _OPINION_RE.search(text) and "clear_opinion" not in hits:
        hits.append("clear_opinion")
    if re.search(r"\b(takeaway|lesson|learned|what I learned)\b", text, re.I) and "lessons_learned" not in hits:
        hits.append("lessons_learned")
    # Specific named tools/projects
    if re.search(r"\b(Qwen|ScholarFlow|RAG|MacBook|Ollama|DeepSeek)\b", text):
        if "specific_details" not in hits:
            hits.append("specific_details")
        if "concrete_examples" not in hits:
            hits.append("concrete_examples")
    return hits


def _inject_verified_memory(memory: dict[str, Any], verified_memory: list[str]) -> dict[str, Any]:
    """Merge caller-supplied verified statements into a memory dict for grounding."""
    projects = list(memory.get("projects") or [])
    for statement in verified_memory:
        # Pull likely project/product names: capitalized tokens and "built X" objects.
        for match in re.finditer(
            r"\b(?:built|building|shipped|using)\s+([A-Z][A-Za-z0-9_-]+)",
            statement,
        ):
            projects.append(match.group(1))
        for match in re.finditer(r"\b([A-Z][A-Za-z0-9_-]{2,})\b", statement):
            token = match.group(1)
            if token.lower() not in {"i", "rag", "using", "the", "and", "for"}:
                # Keep product-like tokens; RAG is also a useful project hint.
                if token[0].isupper():
                    projects.append(token)
        if "RAG" in statement and "RAG" not in projects:
            projects.append("RAG")
    return {
        **memory,
        "verified_experiences": [
            {
                "id": f"inj_{i}",
                "statement": statement,
                "approved": True,
                "reusable": True,
                "category": "project",
                "source": "user_provided",
            }
            for i, statement in enumerate(verified_memory)
        ],
        "experiences": list(
            dict.fromkeys(list(memory.get("experiences") or []) + list(verified_memory))
        ),
        "projects": list(dict.fromkeys(projects)),
    }


def _score(
    text: str,
    detected: list[DetectedPattern],
    preferred: list[str],
) -> tuple[int, int, int, int]:
    if not text.strip():
        return 0, 100, 0, 0

    risk = 15
    for pattern in detected:
        risk += _SEVERITY_WEIGHT.get(pattern.severity, 10)
    # Cap and boost for stacked high-severity patterns
    high_count = sum(1 for p in detected if p.severity in {"high", "critical"})
    if high_count >= 2:
        risk += 12
    if any(p.category == "generic_opening" for p in detected) and not preferred:
        risk = max(risk, 78)
    if any(p.category == "vague_claims" for p in detected):
        risk = max(risk, 72)
    if any(p.category == "fake_sources" for p in detected):
        risk = max(risk, 80)
    ai_pattern_risk = clamp_score(risk)

    human = 52
    human += 10 * len(preferred)
    if _FIRST_PERSON_RE.search(text):
        human += 12
    if any(p.category == "lack_of_personal_voice" for p in detected):
        human -= 25
    if any(p.category == "generic_opening" for p in detected):
        human -= 22
    if any(p.category in {"buzzword_overuse", "inflated_language"} for p in detected):
        human -= 12
    if any(p.category in {"vague_claims", "fake_sources"} for p in detected):
        human -= 15
    if ai_pattern_risk >= 70:
        human = min(human, 38)
    human_quality_score = clamp_score(human)

    specificity = 30
    specificity += 12 * len([p for p in preferred if p in {"specific_details", "concrete_examples"}])
    if re.search(r"\b(Qwen|ScholarFlow|RAG|MacBook|Ollama|evaluation loop|workflow)\b", text, re.I):
        specificity += 20
    if any(p.category in {"vague_claims", "fake_sources"} for p in detected):
        specificity -= 25
    specificity_score = clamp_score(specificity)

    originality = 45
    originality += 10 * len([p for p in preferred if p in {"clear_opinion", "lessons_learned", "personal_observation"}])
    if any(p.category in {"formulaic_structure", "repetition", "generic_opening"} for p in detected):
        originality -= 20
    originality_score = clamp_score(originality)

    return human_quality_score, ai_pattern_risk, specificity_score, originality_score


def _default_improvements(detected: list[DetectedPattern], preferred: list[str]) -> list[str]:
    improvements: list[str] = []
    categories = {p.category for p in detected}
    if "generic_opening" in categories:
        improvements.append("Replace the generic opening with a specific observation or opinion.")
    if "editorial_commentary" in categories:
        improvements.append("Cut meta commentary; state the insight directly.")
    if "vague_claims" in categories:
        improvements.append("Replace vague claims with a source, example, or verified experience.")
    if "buzzword_overuse" in categories or "inflated_language" in categories:
        improvements.append("Swap hype words for plain operational language.")
    if "unnatural_certainty" in categories:
        improvements.append("Soften absolute claims with experience-based hedging (likely / in my experience).")
    if "lack_of_personal_voice" in categories:
        improvements.append("Add a personal observation or lesson grounded in verified memory.")
    if "formulaic_structure" in categories or "excessive_formatting" in categories:
        improvements.append("Reduce template structure; write in short prose paragraphs.")
    if "repetition" in categories:
        improvements.append("Remove repeated ideas and redundant conclusions.")
    if not preferred:
        improvements.append("Include one concrete detail (tool, experiment, or failure) from verified memory.")
    # Deduplicate
    out: list[str] = []
    for item in improvements:
        if item not in out:
            out.append(item)
    return out[:6]


def analyze_writing_quality(
    content: str,
    *,
    content_mode: str = "founder",
    verified_memory: list[str] | None = None,
    user_memory: dict[str, Any] | None = None,
) -> WritingQualityOutput:
    """Deterministic writing-quality analysis (pattern risk, not AI detection)."""
    text = (content or "").strip()
    memory = user_memory or load_user_memory()
    if verified_memory is not None:
        memory = _inject_verified_memory(memory, verified_memory)

    guidelines = load_ai_writing_guidelines()
    categories = _category_map(guidelines)
    detected: list[DetectedPattern] = []

    _detect_phrase_categories(
        text,
        categories,
        ["generic_opening", "editorial_commentary", "vague_claims", "buzzword_overuse"],
        detected,
    )

    # Buzzword threshold: count distinct buzzwords
    buzz_meta = categories.get("buzzword_overuse") or {}
    buzz_examples = [str(x) for x in buzz_meta.get("examples", [])]
    buzz_hits = [b for b in buzz_examples if b.lower() in text.lower()]
    threshold = int(buzz_meta.get("threshold", 2))
    if len(set(x.lower() for x in buzz_hits)) >= threshold:
        # Ensure category present even if phrase loop already added some.
        if not any(p.category == "buzzword_overuse" for p in detected):
            _add_pattern(
                detected,
                category="buzzword_overuse",
                severity=str(buzz_meta.get("severity", "high")),
                example=", ".join(buzz_hits[:4]),
                explanation=str(buzz_meta.get("problem", "Buzzword overuse")),
            )

    for match in _INFLATED_RE.finditer(text):
        meta = categories.get("inflated_language") or {}
        _add_pattern(
            detected,
            category="inflated_language",
            severity=str(meta.get("severity", "medium")),
            example=match.group(0),
            explanation=str(meta.get("problem", "Inflated language")),
        )

    for match in _CERTAINTY_RE.finditer(text):
        meta = categories.get("unnatural_certainty") or {}
        _add_pattern(
            detected,
            category="unnatural_certainty",
            severity=str(meta.get("severity", "high")),
            example=match.group(0),
            explanation=str(meta.get("problem", "Unnatural certainty")),
        )

    _detect_repetition(text, categories, detected)
    _detect_formulaic(text, categories, detected)
    _detect_formatting(text, categories, detected)
    truth_improvements = _detect_truth_integrated(text, memory, categories, detected)

    preferred = _preferred_hits(text, guidelines)
    if text and not preferred and not _FIRST_PERSON_RE.search(text):
        meta = categories.get("lack_of_personal_voice") or {}
        _add_pattern(
            detected,
            category="lack_of_personal_voice",
            severity=str(meta.get("severity", "high")),
            example=text.split(".")[0][:120] if text else "",
            explanation=str(meta.get("problem", "No personal voice")),
        )
    elif text and _FIRST_PERSON_RE.search(text) is None and "personal_observation" not in preferred:
        # First person present elsewhere check already failed — also flag thin impersonal prose.
        if not _OPINION_RE.search(text):
            meta = categories.get("lack_of_personal_voice") or {}
            _add_pattern(
                detected,
                category="lack_of_personal_voice",
                severity=str(meta.get("severity", "high")),
                example="missing personal observation/opinion",
                explanation=str(meta.get("problem", "No personal voice")),
            )

    human, risk, specificity, originality = _score(text, detected, preferred)
    improvements = _default_improvements(detected, preferred) + truth_improvements
    deduped: list[str] = []
    for item in improvements:
        if item not in deduped:
            deduped.append(item)

    report = {
        "human_quality_score": human,
        "ai_pattern_risk": risk,
        "specificity_score": specificity,
        "originality_score": originality,
        "detected_patterns": [p.model_dump() for p in detected],
        "improvements": deduped[:8],
        "preferred_patterns_found": preferred,
        "content_mode": content_mode,
        "disclaimer": guidelines.get(
            "disclaimer",
            "Scores describe writing-pattern risk only; never claim authorship.",
        ),
    }

    return WritingQualityOutput(
        text=text,
        human_quality_score=human,
        ai_pattern_risk=risk,
        specificity_score=specificity,
        originality_score=originality,
        detected_patterns=detected,
        improvements=deduped[:8],
        data=report,
        meta={"deterministic": True, "framework": "ai_writing_quality"},
    )


class WritingQualityAnalyzer:
    """Agent-style wrapper; detection is deterministic, LLM may refine improvements."""

    name = "writing_quality_analyzer"

    def __init__(self, provider: ModelProvider | None = None) -> None:
        self.provider = provider

    async def run(self, payload: WritingQualityInput) -> WritingQualityOutput:
        content = payload.resolved_content()
        memory = payload.user_memory or load_user_memory()
        verified = payload.verified_memory or allowed_experience_texts(memory)
        result = analyze_writing_quality(
            content,
            content_mode=payload.content_mode or "founder",
            verified_memory=verified,
            user_memory=memory,
        )

        if self.provider is None or not content:
            return result

        # Optional enrichment — never override deterministic pattern detection.
        try:
            prompt = build_enrichment_user_prompt(
                content=content,
                content_mode=payload.content_mode or "founder",
                detected_patterns=[p.model_dump() for p in result.detected_patterns],
                preferred_hits=list(result.data.get("preferred_patterns_found") or []),
            )
            llm = await self.provider.generate(
                [
                    ChatMessage(role="system", content=SYSTEM_PROMPT),
                    ChatMessage(role="user", content=prompt),
                ],
                temperature=0.1,
                response_format="json",
            )
            parsed = json.loads(llm.text)
            extra = [str(x) for x in parsed.get("improvements", []) if str(x).strip()]
            merged = list(result.improvements)
            for item in extra:
                if item not in merged:
                    merged.append(item)
            result.improvements = merged[:8]
            result.data["improvements"] = result.improvements
            result.meta = {
                **result.meta,
                "provider": llm.provider,
                "model": llm.model,
                "llm_enriched": True,
            }
        except (json.JSONDecodeError, TypeError, ValueError, AttributeError):
            result.meta = {**result.meta, "llm_enriched": False}

        return result


# Backward-friendly alias used by pipeline imports.
WritingQualityAgent = WritingQualityAnalyzer
