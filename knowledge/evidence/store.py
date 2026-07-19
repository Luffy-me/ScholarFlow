"""Evidence graph store — every claim must have sources."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from shared.knowledge import ROOT

DEFAULT_PATH = ROOT / "knowledge" / "evidence" / "evidence_graph.json"


class EvidenceStore:
    def __init__(self, path: Path | None = None) -> None:
        self.path = path or DEFAULT_PATH
        self.path.parent.mkdir(parents=True, exist_ok=True)
        if not self.path.exists():
            self._write({"claims": []})

    def _read(self) -> dict[str, Any]:
        with self.path.open(encoding="utf-8") as handle:
            data = json.load(handle)
        if not isinstance(data, dict):
            return {"claims": []}
        data.setdefault("claims", [])
        return data

    def _write(self, data: dict[str, Any]) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.path.open("w", encoding="utf-8") as handle:
            json.dump(data, handle, indent=2, ensure_ascii=False)
            handle.write("\n")

    def upsert(self, claim: dict[str, Any]) -> dict[str, Any]:
        data = self._read()
        text = str(claim.get("claim", "")).strip()
        if not text:
            raise ValueError("claim text required")
        now = datetime.now(timezone.utc).isoformat()
        record = {
            "claim": text,
            "supporting_sources": list(claim.get("supporting_sources") or []),
            "contradicting_sources": list(claim.get("contradicting_sources") or []),
            "confidence": float(claim.get("confidence") or 0.0),
            "last_verified": str(claim.get("last_verified") or now),
            "verified": bool(claim.get("verified", False)),
        }
        claims = data["claims"]
        for idx, existing in enumerate(claims):
            if str(existing.get("claim", "")).strip().lower() == text.lower():
                # Merge sources
                support = list(
                    dict.fromkeys(
                        list(existing.get("supporting_sources") or [])
                        + record["supporting_sources"]
                    )
                )
                contra = list(
                    dict.fromkeys(
                        list(existing.get("contradicting_sources") or [])
                        + record["contradicting_sources"]
                    )
                )
                record["supporting_sources"] = support
                record["contradicting_sources"] = contra
                record["confidence"] = max(float(existing.get("confidence") or 0), record["confidence"])
                record["verified"] = bool(existing.get("verified")) or record["verified"]
                claims[idx] = record
                self._write(data)
                return record
        claims.append(record)
        self._write(data)
        return record

    def list_claims(self, *, verified_only: bool = False) -> list[dict[str, Any]]:
        claims = list(self._read().get("claims") or [])
        if verified_only:
            return [c for c in claims if c.get("verified")]
        return claims

    def writer_allowed_claims(self) -> list[dict[str, Any]]:
        """Writer may use verified claims, or clearly attributed opinions."""
        allowed: list[dict[str, Any]] = []
        for claim in self.list_claims():
            if claim.get("verified"):
                allowed.append(claim)
            elif claim.get("supporting_sources"):
                # Attributed opinion — mark for attribution requirement.
                allowed.append({**claim, "attribution_required": True})
        return allowed
