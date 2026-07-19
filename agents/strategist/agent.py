"""Phase 3 stub — Content Strategist contract."""

from agents.base import Agent, AgentInput, AgentOutput


class StrategistAgent(Agent[AgentInput, AgentOutput]):
    name = "strategist"

    async def run(self, payload: AgentInput) -> AgentOutput:
        return AgentOutput(
            data={
                "audience": "",
                "hook": "",
                "opinion": "",
                "structure": "",
                "discussion_question": "",
                "status": "stub",
            },
            meta={"phase": 3},
        )
