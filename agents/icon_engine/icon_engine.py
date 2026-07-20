"""Icon Engine — select icon IDs only (no rendering)."""

from __future__ import annotations

import json
from functools import lru_cache
from typing import Any

from shared.knowledge import ROOT

ICONS_PATH = ROOT / "design" / "icons.json"

LIBRARIES = ("lucide", "heroicons", "material", "phosphor", "tabler")


@lru_cache(maxsize=1)
def _icons_config() -> dict[str, Any]:
    with ICONS_PATH.open(encoding="utf-8") as handle:
        data = json.load(handle)
    return data if isinstance(data, dict) else {}


class IconEngine:
    name = "icon_engine"

    def __init__(self, library: str = "lucide") -> None:
        cfg = _icons_config()
        allowed = set(cfg.get("libraries") or LIBRARIES)
        self.library = library if library in allowed else str(cfg.get("default_library") or "lucide")
        self.aliases = dict(cfg.get("aliases") or {})

    def select(self, role_or_concept: str) -> str:
        """Return an icon id like 'lucide:lightbulb'."""
        key = (role_or_concept or "").strip().lower()
        alias = self.aliases.get(key) or self.aliases.get(key.replace(" ", "_"))
        if not alias:
            # deterministic fallback from concept tokens
            for token, icon in self.aliases.items():
                if token in key:
                    alias = icon
                    break
        alias = alias or "circle"
        return f"{self.library}:{alias}"

    def select_many(self, concepts: list[str]) -> list[str]:
        return [self.select(c) for c in concepts]
