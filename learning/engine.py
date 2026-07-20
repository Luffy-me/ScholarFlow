"""Learning engine — store post-publish recommendations only.

Never automatically modifies prompts.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from shared.knowledge import ROOT

DEFAULT_PATH = ROOT / "learning" / "recommendations.json"


class LearningEngine:
    def __init__(self, path: Path | None = None) -> None:
        self.path = path or DEFAULT_PATH
        self.path.parent.mkdir(parents=True, exist_ok=True)
        if not self.path.exists():
            self._write({"recommendations": [], "events": []})

    def _read(self) -> dict[str, Any]:
        with self.path.open(encoding="utf-8") as handle:
            data = json.load(handle)
        if not isinstance(data, dict):
            return {"recommendations": [], "events": []}
        data.setdefault("recommendations", [])
        data.setdefault("events", [])
        return data

    def _write(self, data: dict[str, Any]) -> None:
        with self.path.open("w", encoding="utf-8") as handle:
            json.dump(data, handle, indent=2, ensure_ascii=False)
            handle.write("\n")

    def record_engagement(
        self,
        *,
        post_id: str,
        text: str,
        likes: int = 0,
        comments: int = 0,
        shares: int = 0,
        saves: int = 0,
        impressions: int = 0,
    ) -> dict[str, Any]:
        data = self._read()
        event = {
            "post_id": post_id,
            "recorded_at": datetime.now(timezone.utc).isoformat(),
            "likes": likes,
            "comments": comments,
            "shares": shares,
            "saves": saves,
            "impressions": impressions,
            "text_length": len(text or ""),
        }
        data["events"].append(event)
        recs = self.extract_recommendations(text=text, metrics=event)
        for rec in recs:
            if rec not in data["recommendations"]:
                data["recommendations"].append(rec)
        self._write(data)
        return {"event": event, "recommendations_added": recs}

    def extract_recommendations(self, *, text: str, metrics: dict[str, Any]) -> list[str]:
        """Derive advisory recommendations only — never rewrite prompts."""
        recs: list[str] = []
        engagement = (
            int(metrics.get("likes") or 0)
            + int(metrics.get("comments") or 0) * 2
            + int(metrics.get("shares") or 0) * 3
            + int(metrics.get("saves") or 0) * 2
        )
        lines = [ln.strip() for ln in (text or "").splitlines() if ln.strip()]
        hook = lines[0] if lines else ""
        length = len(text or "")

        if engagement >= 10 and hook:
            recs.append(f"Successful hook pattern: start with a concrete observation like '{hook[:80]}'")
        if engagement >= 10 and "?" in (text or ""):
            recs.append("Successful CTA pattern: end with a discussion question")
        if 400 <= length <= 1400 and engagement >= 5:
            recs.append("Successful post length band: ~400-1400 characters")
        if engagement >= 8:
            recs.append("Successful structure: short paragraphs with one clear takeaway")
        if not recs:
            recs.append("Collect more engagement samples before changing strategy")
        return recs

    def recommendations(self) -> list[str]:
        return list(self._read().get("recommendations") or [])
