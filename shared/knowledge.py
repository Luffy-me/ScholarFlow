"""Shared path helpers and knowledge loaders."""

from __future__ import annotations

import json
import re
from functools import lru_cache
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
KNOWLEDGE_DIR = ROOT / "knowledge"


def repo_path(*parts: str) -> Path:
    return ROOT.joinpath(*parts)


@lru_cache(maxsize=16)
def load_json(relative_path: str) -> dict[str, Any]:
    path = repo_path(relative_path)
    with path.open(encoding="utf-8") as handle:
        data = json.loads(handle.read())
    if not isinstance(data, dict):
        raise ValueError(f"Expected object in {relative_path}")
    return data


def load_user_memory() -> dict[str, Any]:
    return load_json("knowledge/user_memory.json")


def load_content_modes() -> dict[str, Any]:
    return load_json("knowledge/content_modes.json")


def load_writing_rules() -> dict[str, Any]:
    return load_json("knowledge/writing_rules.json")


def load_banned_patterns() -> dict[str, Any]:
    return load_json("knowledge/banned_patterns.json")


def load_good_posts() -> dict[str, Any]:
    return load_json("knowledge/examples/good_posts.json")


def load_bad_posts() -> dict[str, Any]:
    return load_json("knowledge/examples/bad_posts.json")


def allowed_experience_texts(memory: dict[str, Any] | None = None) -> list[str]:
    mem = memory or load_user_memory()
    values: list[str] = []
    for key in ("background", "skills", "projects", "experiences"):
        items = mem.get(key, [])
        if isinstance(items, list):
            values.extend(str(item) for item in items)
    return values


def clear_knowledge_cache() -> None:
    load_json.cache_clear()
