"""Extract evidence-backed claims from ranked sources."""

from __future__ import annotations

from datetime import datetime, timezone

from agents.research.schemas import EvidenceClaim, RankedSource
from connectors.base import SourceDocument
from models.capabilities import Capability


class EvidenceExtractor:
    name = "research_extractor"
    capabilities = [Capability.EXTRACTION]

    def extract(
        self,
        documents: list[SourceDocument],
        ranked: list[RankedSource] | None = None,
    ) -> list[EvidenceClaim]:
        now = datetime.now(timezone.utc).isoformat()
        claims: list[EvidenceClaim] = []
        for doc in documents:
            text = (doc.content or doc.snippet or doc.title).strip()
            if not text:
                continue
            # Deterministic claim seed from first substantial sentence.
            sentence = next(
                (s.strip() for s in text.replace("!", ".").split(".") if len(s.strip()) > 24),
                text[:160],
            )
            verified = doc.tier == 1 and doc.confidence >= 0.7
            claims.append(
                EvidenceClaim(
                    claim=sentence,
                    supporting_sources=[doc.id or doc.url or doc.title],
                    contradicting_sources=[],
                    confidence=round(float(doc.confidence), 3),
                    last_verified=now,
                    verified=verified,
                )
            )
        # Prefer higher-confidence unique claims.
        deduped: list[EvidenceClaim] = []
        seen: set[str] = set()
        for claim in sorted(claims, key=lambda c: (-c.confidence, -int(c.verified))):
            key = claim.claim.lower()
            if key in seen:
                continue
            seen.add(key)
            deduped.append(claim)
        return deduped[:12]
