"""Verified Experience Memory Builder.

Converts user-provided experiences into verified memories.
Never invents or auto-creates experiences — only user-approved facts are reusable.
"""

from __future__ import annotations

import json
import re
import uuid
from datetime import datetime, timezone
from typing import Any, Literal

from pydantic import BaseModel, Field

from agents.base import Agent, AgentInput, AgentOutput
from models.base import ModelProvider
from models.fake import FakeProvider
from shared.knowledge import clear_knowledge_cache, load_user_memory, repo_path


ExperienceCategory = Literal[
    "project",
    "experiment",
    "lesson",
    "skill",
    "background",
    "achievement",
    "other",
]


class ExperienceRecord(BaseModel):
    id: str
    statement: str
    category: ExperienceCategory = "other"
    source: str = "user_provided"
    approved: bool = False
    approved_at: str | None = None
    tags: list[str] = Field(default_factory=list)
    reusable: bool = False
    related_projects: list[str] = Field(default_factory=list)


class MemoryBuilderInput(AgentInput):
    action: str = "list_verified"  # propose | approve | reject | list_verified | list_pending
    statement: str = ""
    category: ExperienceCategory = "other"
    experience_id: str = ""
    tags: list[str] = Field(default_factory=list)
    related_projects: list[str] = Field(default_factory=list)
    persist: bool = False


class MemoryBuilderOutput(AgentOutput):
    verified: list[dict[str, Any]] = Field(default_factory=list)
    pending: list[dict[str, Any]] = Field(default_factory=list)
    changed: dict[str, Any] = Field(default_factory=dict)


def _utcnow() -> str:
    return datetime.now(timezone.utc).isoformat()


def _new_id(prefix: str = "exp") -> str:
    return f"{prefix}_{uuid.uuid4().hex[:10]}"


def _slug_id(statement: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "_", statement.lower()).strip("_")[:40]
    return f"exp_{slug}" if slug else _new_id()


def normalize_memory(memory: dict[str, Any] | None = None) -> dict[str, Any]:
    """Ensure verified/pending experience collections exist without inventing facts."""
    mem = dict(memory or load_user_memory())
    mem.setdefault("schema_version", "2.0")
    mem.setdefault("verified_experiences", [])
    mem.setdefault("pending_experiences", [])
    mem.setdefault(
        "memory_policy",
        {
            "never_auto_create_experiences": True,
            "only_user_approved_facts_reusable": True,
            "unapproved_experiences_forbidden_in_generation": True,
        },
    )

    # Migrate legacy plain-string experiences into verified records if missing.
    # Only migrates existing user-authored strings — never invents new ones.
    existing_statements = {
        str(item.get("statement", "")).strip().lower()
        for item in mem.get("verified_experiences", [])
        if isinstance(item, dict)
    }
    for statement in mem.get("experiences") or []:
        text = str(statement).strip()
        if not text or text.lower() in existing_statements:
            continue
        mem["verified_experiences"].append(
            ExperienceRecord(
                id=_slug_id(text),
                statement=text,
                category="other",
                source="user_provided_legacy",
                approved=True,
                approved_at=mem.get("migrated_at") or _utcnow(),
                tags=[],
                reusable=True,
            ).model_dump()
        )
        existing_statements.add(text.lower())

    # Projects as verified project facts (user-authored list only).
    for project in mem.get("projects") or []:
        text = f"Built a {project}" if not str(project).lower().startswith("built") else str(project)
        # Prefer exact project name as reusable fact too.
        for candidate in (str(project).strip(), text):
            if not candidate or candidate.lower() in existing_statements:
                continue
            # Only add the bare project name as a verified project fact.
            if candidate == str(project).strip():
                mem["verified_experiences"].append(
                    ExperienceRecord(
                        id=_slug_id(f"project_{candidate}"),
                        statement=candidate,
                        category="project",
                        source="user_provided_legacy",
                        approved=True,
                        approved_at=_utcnow(),
                        tags=[candidate],
                        reusable=True,
                        related_projects=[candidate],
                    ).model_dump()
                )
                existing_statements.add(candidate.lower())
            break

    return mem


def list_verified_experiences(memory: dict[str, Any] | None = None) -> list[dict[str, Any]]:
    mem = normalize_memory(memory)
    return [
        item
        for item in mem.get("verified_experiences", [])
        if isinstance(item, dict) and item.get("approved") is True and item.get("reusable", True)
    ]


def list_pending_experiences(memory: dict[str, Any] | None = None) -> list[dict[str, Any]]:
    mem = normalize_memory(memory)
    return [item for item in mem.get("pending_experiences", []) if isinstance(item, dict)]


def approved_experience_texts(memory: dict[str, Any] | None = None) -> list[str]:
    """Texts agents may reuse. Unapproved pending facts are excluded."""
    values: list[str] = []
    for item in list_verified_experiences(memory):
        statement = str(item.get("statement", "")).strip()
        if statement:
            values.append(statement)
        for project in item.get("related_projects") or []:
            if str(project).strip():
                values.append(str(project).strip())
    # Keep skills/background as soft context (non-anecdotal).
    mem = normalize_memory(memory)
    for key in ("background", "skills", "projects"):
        for item in mem.get(key) or []:
            if str(item).strip():
                values.append(str(item).strip())
    # Deduplicate preserving order
    seen: set[str] = set()
    out: list[str] = []
    for value in values:
        key = value.lower()
        if key in seen:
            continue
        seen.add(key)
        out.append(value)
    return out


def is_experience_approved(statement: str, memory: dict[str, Any] | None = None) -> bool:
    needle = statement.strip().lower()
    if not needle:
        return False
    for item in list_verified_experiences(memory):
        approved_stmt = str(item.get("statement", "")).strip().lower()
        if needle == approved_stmt or needle in approved_stmt or approved_stmt in needle:
            return True
        for project in item.get("related_projects") or []:
            if needle == str(project).strip().lower():
                return True
    return False


def propose_experience(
    statement: str,
    *,
    category: ExperienceCategory = "other",
    tags: list[str] | None = None,
    related_projects: list[str] | None = None,
    memory: dict[str, Any] | None = None,
) -> tuple[dict[str, Any], dict[str, Any]]:
    """Add a user-provided experience to pending. Never auto-approves."""
    mem = normalize_memory(memory)
    text = statement.strip()
    if not text:
        raise ValueError("Experience statement is required")

    # Refuse duplicates already verified.
    if is_experience_approved(text, mem):
        raise ValueError("Experience already verified/approved")

    pending = list_pending_experiences(mem)
    for item in pending:
        if str(item.get("statement", "")).strip().lower() == text.lower():
            return mem, item

    record = ExperienceRecord(
        id=_new_id("pending"),
        statement=text,
        category=category,
        source="user_provided",
        approved=False,
        approved_at=None,
        tags=tags or [],
        reusable=False,
        related_projects=related_projects or [],
    ).model_dump()
    mem.setdefault("pending_experiences", []).append(record)
    return mem, record


def approve_experience(
    experience_id: str,
    *,
    memory: dict[str, Any] | None = None,
) -> tuple[dict[str, Any], dict[str, Any]]:
    mem = normalize_memory(memory)
    pending = mem.get("pending_experiences") or []
    found: dict[str, Any] | None = None
    remaining: list[dict[str, Any]] = []
    for item in pending:
        if str(item.get("id")) == experience_id:
            found = dict(item)
        else:
            remaining.append(item)
    if not found:
        raise ValueError(f"Pending experience not found: {experience_id}")

    found["approved"] = True
    found["reusable"] = True
    found["approved_at"] = _utcnow()
    found["id"] = found.get("id", _new_id()).replace("pending_", "exp_")
    mem["pending_experiences"] = remaining
    mem.setdefault("verified_experiences", []).append(found)

    # Mirror into legacy experiences list for compatibility.
    statement = str(found.get("statement", "")).strip()
    legacy = [str(x) for x in (mem.get("experiences") or [])]
    if statement and statement not in legacy:
        legacy.append(statement)
        mem["experiences"] = legacy
    return mem, found


def reject_experience(
    experience_id: str,
    *,
    memory: dict[str, Any] | None = None,
) -> tuple[dict[str, Any], dict[str, Any]]:
    mem = normalize_memory(memory)
    pending = mem.get("pending_experiences") or []
    found: dict[str, Any] | None = None
    remaining: list[dict[str, Any]] = []
    for item in pending:
        if str(item.get("id")) == experience_id:
            found = dict(item)
        else:
            remaining.append(item)
    if not found:
        raise ValueError(f"Pending experience not found: {experience_id}")
    mem["pending_experiences"] = remaining
    return mem, found


def save_user_memory(memory: dict[str, Any], path: str = "knowledge/user_memory.json") -> None:
    target = repo_path(path)
    target.write_text(json.dumps(memory, indent=2) + "\n", encoding="utf-8")
    clear_knowledge_cache()


class MemoryBuilderAgent(Agent[MemoryBuilderInput, MemoryBuilderOutput]):
    """Manages verified experience memory. Never auto-creates facts."""

    name = "memory_builder"

    def __init__(self, provider: ModelProvider | None = None) -> None:
        super().__init__(provider or FakeProvider())

    async def run(self, payload: MemoryBuilderInput) -> MemoryBuilderOutput:
        # Explicitly ignore LLM generation — memory is user-authored only.
        memory = normalize_memory(payload.user_memory or load_user_memory())
        changed: dict[str, Any] = {}

        if payload.action == "propose":
            memory, changed = propose_experience(
                payload.statement,
                category=payload.category,
                tags=payload.tags,
                related_projects=payload.related_projects,
                memory=memory,
            )
        elif payload.action == "approve":
            memory, changed = approve_experience(payload.experience_id, memory=memory)
        elif payload.action == "reject":
            memory, changed = reject_experience(payload.experience_id, memory=memory)
        elif payload.action in {"list_verified", "list_pending"}:
            changed = {"action": payload.action}
        else:
            raise ValueError(f"Unknown memory builder action: {payload.action}")

        if payload.persist and payload.action in {"propose", "approve", "reject"}:
            save_user_memory(memory)

        verified = list_verified_experiences(memory)
        pending = list_pending_experiences(memory)
        return MemoryBuilderOutput(
            text="",
            verified=verified,
            pending=pending,
            changed=changed,
            data={
                "verified_experiences": verified,
                "pending_experiences": pending,
                "changed": changed,
                "memory_policy": memory.get("memory_policy", {}),
            },
            meta={"agent": self.name, "deterministic": True, "auto_create": False},
        )
