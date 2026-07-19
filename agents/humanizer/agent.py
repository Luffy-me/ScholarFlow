"""Human Voice Agent — rewrite toward authentic first-person writing.

Truth Layer v2 constraint:
Humanizer may only improve wording, structure, and clarity.
It must NEVER invent experiences, metrics, clients, or achievements.
"""

from __future__ import annotations

from agents.base import Agent, AgentInput, AgentOutput
from agents.grounding import check_claims
from models.base import ChatMessage
from shared.knowledge import allowed_experience_texts, load_user_memory
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
        allowed = allowed_experience_texts(memory)
        system = (
            "You are a humanizing editor for LinkedIn drafts.\n"
            "You may ONLY:\n"
            "- improve wording\n"
            "- improve structure\n"
            "- improve clarity\n"
            "You must NOT invent or add:\n"
            "- experiences\n"
            "- metrics or percentages\n"
            "- clients or customers\n"
            "- achievements\n"
            "- quotes\n"
            "- specific time references not already in the draft\n"
            "Prefer first person when already present.\n"
            "Remove corporate language and fake enthusiasm.\n"
            f"Allowed experiences (do not expand beyond these): {allowed}\n"
            "If the draft is sparse after grounding, keep it sparse. Do not fill gaps with fiction."
        )
        result = await self.provider.generate(
            [
                ChatMessage(role="system", content=system),
                ChatMessage(role="user", content=source or "No draft provided."),
            ],
            temperature=0.3,
        )
        rewritten = result.text.strip() or source
        rewritten = rewritten.replace("```markdown", "").replace("```", "").strip()

        # Hard guard: if humanizer invents claims, revert to grounded source.
        rewritten_check = check_claims(rewritten, memory)
        source_check = check_claims(source, memory)
        if (not rewritten_check.safe) and source_check.safe:
            rewritten = source
        elif not rewritten_check.safe:
            rewritten = self._deterministic_humanize(source, memory)

        scan = scan_text(rewritten, memory)
        if (not rewritten) or (scan.has_generic_ai and not scan.has_strong_first_person):
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
                },
                "grounding_safe": check_claims(rewritten, memory).safe,
            },
            meta={"provider": result.provider, "model": result.model},
        )

    def _deterministic_humanize(self, text: str, memory: dict) -> str:
        # Style-only rewrite: never introduce new facts/metrics/clients.
        base = (text or "").strip()
        scan = scan_text(base, memory)
        if base and not scan.has_generic_ai and scan.first_person_count >= 1:
            return base

        projects = memory.get("projects") or []
        project = projects[0] if projects else "recent work"
        # If we only have toxic generic source text, replace with a grounded scaffold.
        return (
            f"I keep coming back to lessons from {project}.\n\n"
            "I want the draft to stay specific, first person, and free of invented metrics.\n\n"
            "What would you cut from your last draft?"
        )


async def humanize_text(provider, *, text: str, user_memory: dict | None = None) -> HumanizerOutput:
    agent = HumanizerAgent(provider)
    return await agent.run(HumanizerInput(text=text, user_memory=user_memory or {}))
