"""LinkedIn Writer Agent."""

from __future__ import annotations

import re
from typing import Any

from agents.base import Agent, AgentInput, AgentOutput
from models.base import ChatMessage
from shared.knowledge import allowed_experience_texts, load_content_modes, load_user_memory, load_writing_rules
from shared.quality import scan_text


class WriterInput(AgentInput):
    pass


class WriterOutput(AgentOutput):
    rejected_fake_experiences: list[str] = []


class WriterAgent(Agent[WriterInput, WriterOutput]):
    name = "writer"

    async def run(self, payload: WriterInput) -> WriterOutput:
        memory = payload.user_memory or load_user_memory()
        modes = load_content_modes()
        mode_key = payload.content_mode if payload.content_mode in modes.get("modes", {}) else modes.get(
            "default_mode", "founder"
        )
        mode = modes["modes"][mode_key]
        allowed = allowed_experience_texts(memory)
        rules = load_writing_rules()

        system = (
            "You are a LinkedIn writing partner for authentic thought leadership.\n"
            "Write in first person when appropriate.\n"
            "Never invent personal experiences.\n"
            "Only use VERIFIED/APPROVED experiences from the allowed list.\n"
            "Never use pending or unapproved experiences.\n"
            "Avoid corporate AI phrases and weak generic openings.\n"
            "Short paragraphs. Specific examples. Clear opinion.\n"
            f"Content mode: {mode_key} — {mode.get('label')}. Tone: {mode.get('tone')}.\n"
            f"Opening guidance: {mode.get('opening_guidance')}\n"
            f"Emphasis: {', '.join(mode.get('emphasis', []))}\n"
            f"Avoid: {', '.join(mode.get('avoid', []))}\n"
            f"Allowed verified experiences: {allowed}\n"
            f"Fallback phrases if no personal experience fits: "
            f"{rules.get('experience_policy', {}).get('fallback_phrases', [])}"
        )
        extra = payload.extra or {}
        audience = str(extra.get("audience") or "").strip()
        angle = extra.get("angle") or {}
        strategy = extra.get("strategy") or {}
        user = (
            f"Topic: {payload.topic}\n"
            f"Format: {payload.format}\n"
        )
        if audience:
            user += f"Audience: {audience}\n"
        if angle:
            user += f"Selected angle: {angle}\n"
        if strategy:
            user += f"Strategy: {strategy}\n"
        user += "Write a LinkedIn post draft now."

        result = await self.provider.generate(
            [ChatMessage(role="system", content=system), ChatMessage(role="user", content=user)],
            temperature=0.5,
        )
        draft = result.text.strip()
        # Strip accidental markdown fences from local models.
        draft = re.sub(r"^```(?:markdown|text)?\s*", "", draft)
        draft = re.sub(r"\s*```$", "", draft).strip()
        draft, rejected = self._strip_ungrounded_claims(draft, allowed)
        scan = scan_text(draft, memory)

        # Soft guard: keep real-model drafts for evaluation unless clearly unusable.
        unusable = (not draft) or scan.has_fake_experience or (
            scan.has_generic_ai and scan.first_person_count == 0
        )
        if unusable or scan.first_person_count == 0:
            draft = self._deterministic_draft(payload.topic, mode_key, allowed, memory)
            rejected = []
            scan = scan_text(draft, memory)

        return WriterOutput(
            text=draft,
            rejected_fake_experiences=rejected,
            data={
                "content_mode": mode_key,
                "format": payload.format,
                "quality_scan": {
                    "generic_ai": scan.has_generic_ai,
                    "weak_hook": scan.has_weak_hook,
                    "fake_experience": scan.has_fake_experience,
                    "first_person": scan.has_strong_first_person,
                },
            },
            meta={"provider": result.provider, "model": result.model},
        )

    def _strip_ungrounded_claims(self, text: str, allowed: list[str]) -> tuple[str, list[str]]:
        rejected: list[str] = []
        patterns = [
            r"I built a million-user[^.]*\.",
            r"I tested this with thousands[^.]*\.",
            r"I scaled to millions[^.]*\.",
            r"I discovered during my research that[^.]*\.",
        ]
        cleaned = text
        for pattern in patterns:
            for match in re.finditer(pattern, cleaned, flags=re.IGNORECASE):
                claim = match.group(0)
                if not any(item.lower() in claim.lower() for item in allowed):
                    rejected.append(claim)
                    cleaned = cleaned.replace(claim, "")
        cleaned = re.sub(r"\n{3,}", "\n\n", cleaned).strip()
        return cleaned, rejected

    def _deterministic_draft(
        self,
        topic: str,
        mode: str,
        allowed: list[str],
        memory: dict[str, Any],
    ) -> str:
        experience = allowed[0] if allowed else "After analyzing this topic"
        style = memory.get("style", {})
        first_person = bool(style.get("first_person", True))
        if first_person and allowed:
            opening = f"I worked on {allowed[0].rstrip('.')} recently, and one lesson stuck."
            body = (
                f"While exploring {topic}, I kept coming back to practical tradeoffs — "
                f"not slogans.\n\n"
                f"From that work ({experience}), the useful insight was simple: "
                f"specific systems beat generic advice.\n\n"
                f"What are you testing on {topic} right now?"
            )
        else:
            opening = f"One interesting pattern I noticed around {topic}:"
            body = (
                f"{opening}\n\n"
                f"After analyzing the details, the lesson was concrete rather than motivational.\n\n"
                f"What pattern are you seeing?"
            )
            return body
        return f"{opening}\n\n{body}"


async def write_post(
    provider,
    *,
    topic: str,
    content_mode: str = "founder",
    format: str = "short",
    user_memory: dict[str, Any] | None = None,
) -> WriterOutput:
    agent = WriterAgent(provider)
    return await agent.run(
        WriterInput(
            topic=topic,
            content_mode=content_mode,
            format=format,
            user_memory=user_memory or {},
        )
    )
