"""Internal helpers for deterministic, evidence-grounded reasoning."""

from __future__ import annotations

import hashlib
import re
from typing import Any


_WORD = re.compile(r"[a-z0-9]{3,}")


def stable_id(prefix: str, *parts: str) -> str:
    digest = hashlib.sha256("|".join(parts).encode("utf-8")).hexdigest()[:10]
    return f"{prefix}:{digest}"


def normalize_text(value: str) -> str:
    return re.sub(r"\s+", " ", (value or "").strip())


def tokens(text: str) -> list[str]:
    return _WORD.findall((text or "").lower())


def claim_ref(claim: dict[str, Any] | str, index: int = 0) -> str:
    if isinstance(claim, str):
        return f"evidence:{index}:{stable_id('c', claim)[2:]}"
    text = normalize_text(str(claim.get("claim") or ""))
    sources = claim.get("supporting_sources") or []
    if sources:
        return str(sources[0])
    return f"evidence:{index}:{stable_id('c', text)[2:]}"


def extract_claims(evidence: Any) -> list[dict[str, Any]]:
    """Normalize evidence graph / research evidence into claim dicts."""
    claims: list[dict[str, Any]] = []
    if evidence is None:
        return claims
    if hasattr(evidence, "list_claims"):
        raw = evidence.list_claims()
        return [c for c in raw if isinstance(c, dict) and normalize_text(str(c.get("claim") or ""))]
    if isinstance(evidence, dict):
        if isinstance(evidence.get("claims"), list):
            items = evidence["claims"]
        elif isinstance(evidence.get("evidence"), list):
            items = evidence["evidence"]
        else:
            items = []
        for item in items:
            if isinstance(item, dict) and normalize_text(str(item.get("claim") or "")):
                claims.append(item)
            elif isinstance(item, str) and normalize_text(item):
                claims.append({"claim": normalize_text(item), "supporting_sources": [], "confidence": 0.4})
        return claims
    if isinstance(evidence, list):
        for item in evidence:
            if isinstance(item, dict) and normalize_text(str(item.get("claim") or "")):
                claims.append(item)
            elif hasattr(item, "model_dump"):
                dumped = item.model_dump()
                if normalize_text(str(dumped.get("claim") or "")):
                    claims.append(dumped)
            elif isinstance(item, str) and normalize_text(item):
                claims.append({"claim": normalize_text(item), "supporting_sources": [], "confidence": 0.4})
    return claims


def extract_trends(trends: Any) -> list[dict[str, Any]]:
    if trends is None:
        return []
    if isinstance(trends, dict):
        if isinstance(trends.get("trends"), list):
            trends = trends["trends"]
        else:
            return []
    out: list[dict[str, Any]] = []
    for item in trends or []:
        if hasattr(item, "model_dump"):
            item = item.model_dump()
        if isinstance(item, dict) and (item.get("trend") or item.get("name")):
            out.append(
                {
                    "trend": normalize_text(str(item.get("trend") or item.get("name") or "")),
                    "momentum": float(item.get("momentum") or 0.0),
                    "confidence": float(item.get("confidence") or 0.0),
                    "supporting_sources": list(item.get("supporting_sources") or []),
                }
            )
        elif isinstance(item, str) and item.strip():
            out.append({"trend": normalize_text(item), "momentum": 0.5, "confidence": 0.4, "supporting_sources": []})
    return out


def extract_research(research: Any) -> dict[str, Any]:
    if research is None:
        return {}
    if hasattr(research, "as_dict"):
        return research.as_dict()
    if hasattr(research, "model_dump"):
        return research.model_dump()
    if isinstance(research, dict):
        return research
    return {}


def extract_opportunity(opportunity: Any) -> dict[str, Any]:
    if opportunity is None:
        return {}
    if hasattr(opportunity, "model_dump"):
        return opportunity.model_dump()
    if isinstance(opportunity, dict):
        return opportunity
    return {}


def knowledge_summary(graph: Any) -> dict[str, Any]:
    if graph is None:
        return {"nodes": [], "edges": [], "labels": []}
    if hasattr(graph, "nodes") and hasattr(graph, "edges"):
        nodes = graph.nodes()
        edges = graph.edges()
    elif isinstance(graph, dict):
        nodes = list(graph.get("nodes") or [])
        edges = list(graph.get("edges") or [])
    else:
        return {"nodes": [], "edges": [], "labels": []}
    labels = sorted(
        {
            normalize_text(str(n.get("label") or ""))
            for n in nodes
            if isinstance(n, dict) and n.get("label")
        }
    )
    contradicts = [
        e
        for e in edges
        if isinstance(e, dict) and str(e.get("relation") or "").lower() == "contradicts"
    ]
    return {"nodes": nodes, "edges": edges, "labels": labels, "contradict_edges": contradicts}


def mean_confidence(claims: list[dict[str, Any]]) -> float:
    if not claims:
        return 0.0
    vals = [float(c.get("confidence") or 0.0) for c in claims]
    return max(0.0, min(1.0, sum(vals) / len(vals)))


def verified_ratio(claims: list[dict[str, Any]]) -> float:
    if not claims:
        return 0.0
    return sum(1 for c in claims if c.get("verified")) / len(claims)


def top_claims(claims: list[dict[str, Any]], *, limit: int = 8) -> list[dict[str, Any]]:
    ranked = sorted(
        claims,
        key=lambda c: (
            1 if c.get("verified") else 0,
            float(c.get("confidence") or 0.0),
            normalize_text(str(c.get("claim") or "")),
        ),
        reverse=True,
    )
    return ranked[:limit]


def topic_or_default(topic: str, research: dict[str, Any]) -> str:
    t = normalize_text(topic)
    if t:
        return t
    return normalize_text(str(research.get("topic") or "untitled topic")) or "untitled topic"


def refs_for_claims(claims: list[dict[str, Any]]) -> list[str]:
    refs: list[str] = []
    for i, claim in enumerate(claims):
        refs.append(claim_ref(claim, i))
        for src in claim.get("supporting_sources") or []:
            if str(src) not in refs:
                refs.append(str(src))
    return refs[:20]


def has_evidence_support(text: str, claims: list[dict[str, Any]]) -> bool:
    """True only when statement tokens overlap evidence — prevents hallucinated facts."""
    text_tokens = set(tokens(text))
    if not text_tokens or not claims:
        return False
    for claim in claims:
        claim_tokens = set(tokens(str(claim.get("claim") or "")))
        if len(text_tokens & claim_tokens) >= 2:
            return True
    return False
