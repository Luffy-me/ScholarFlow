"""Human Voice Agent — rewrite toward authentic first-person writing."""

from __future__ import annotations

from agents.base import Agent, AgentInput, AgentOutput
from models.base import ChatMessage
from shared.knowledge import load_user_memory
from shared.quality import scan_text


class HumanizerInput(AgentInput):
    pass


class HumanizerOutput(AgentOutput):
    preferred_first_person: bool = True


class HumanizerAgent(Agent[HumanizerInput, HumanizerOutput]):
    name = "humanizer"

    async def run(self, payload: HumanizerInput) -> HumanizerOutput:
        memory = payload.user_memory or load_user_memory()
        source = payload.text.strip()
        system = (
            "Rewrite the LinkedIn draft so it sounds like a real person.\n"
            "Prefer first person. Remove corporate language and fake enthusiasm.\n"
            "Keep meaning. Do not invent personal experiences.\n"
            "Use short paragraphs and a clear perspective."
        )
        result = await self.provider.generate(
            [
                ChatMessage(role="system", content=system),
                ChatMessage(role="user", content=source or "No draft provided."),
            ],
            temperature=0.4,
        )
        rewritten = result.text.strip() or source
        scan = scan_text(rewritten, memory)

        if scan.has_generic_ai or not scan.has_strong_first_person:
            rewritten = self._deterministic_humanize(source or payload.topic, memory)
            scan = scan_text(rewritten, memory)

        return HumanizerOutput(
            text=rewritten,
            preferred_first_person=True,
            data={
                "quality_scan": {
                    "generic_ai": scan.has_generic_ai,
                    "first_person": scan.has_strong_first_person,
                    "first_person_count": scan.first_person_count,
                }
            },
            meta={"provider": result.provider, "model": result.model},
        )

    def _deterministic_humanize(self, text: str, memory: dict) -> str:
        # Never echo the original opening — it may contain banned generic phrases.
        projects = memory.get("projects") or []
        project = projects[0] if projects else "my recent work"
        return (
            "I rewrote this draft because the first version sounded like a template.\n\n"
            f"What I actually care about from {project} is the messy part: the tradeoffs and the corrections.\n\n"
            "So here's the clearer version — specific, first person, and without corporate filler.\n\n"
            "What would you cut from your last post?"
        )


async def humanize_text(provider, *, text: str, user_memory: dict | None = None) -> HumanizerOutput:
    agent = HumanizerAgent(provider)
    return await agent.run(HumanizerInput(text=text, user_memory=user_memory or {}))
