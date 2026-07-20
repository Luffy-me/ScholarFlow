"""Human Voice Agent — rewrite toward authentic first-person writing.

AI Writing Quality Framework constraints:
Humanizer may:
- improve clarity
- improve sentence flow
- remove generic phrases
- make tone natural

Humanizer must NOT:
- create experiences
- add achievements
- add metrics
- add emotions that did not exist
- invent stories
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
        improvements = []
        if isinstance(payload.extra, dict):
            improvements = [str(x) for x in payload.extra.get("improvements", []) if str(x).strip()]

        system = (
            "You are a humanizing editor for LinkedIn drafts.\n"
            "You may ONLY:\n"
            "- improve clarity\n"
            "- improve sentence flow\n"
            "- remove generic phrases\n"
            "- make tone natural\n"
            "You must NOT:\n"
            "- create experiences\n"
            "- add achievements\n"
            "- add metrics\n"
            "- add emotions that did not exist in the draft\n"
            "- invent stories\n"
            "- add clients, quotes, or time references not already present\n"
            "Prefer first person when already present.\n"
            "Remove corporate language and fake enthusiasm.\n"
            f"Allowed experiences (do not expand beyond these): {allowed}\n"
        )
        if improvements:
            system += (
                "Apply these writing-quality improvements when possible without inventing facts:\n"
                + "\n".join(f"- {item}" for item in improvements[:6])
                + "\n"
            )
        system += (
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
                "applied_improvements": improvements,
            },
            meta={"provider": result.provider, "model": result.model},
        )

    def _deterministic_humanize(self, text: str, memory: dict) -> str:
        # Style-only rewrite: never introduce new facts/metrics/clients/emotions/stories.
        base = (text or "").strip()
        scan = scan_text(base, memory)
        if base and not scan.has_generic_ai and scan.first_person_count >= 1:
            return base

        projects = memory.get("projects") or []
        project = projects[0] if projects else "recent work"
        return (
            f"I keep coming back to lessons from {project}.\n\n"
            "I want the draft to stay specific, first person, and free of invented metrics.\n\n"
            "What would you cut from your last draft?"
        )


async def humanize_text(provider, *, text: str, user_memory: dict | None = None) -> HumanizerOutput:
    agent = HumanizerAgent(provider)
    return await agent.run(HumanizerInput(text=text, user_memory=user_memory or {}))
