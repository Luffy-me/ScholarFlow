"""Phase 3 stub — Carousel Designer contract."""

from agents.base import Agent, AgentInput, AgentOutput


class DesignerAgent(Agent[AgentInput, AgentOutput]):
    name = "designer"

    async def run(self, payload: AgentInput) -> AgentOutput:
        return AgentOutput(
            data={"slides": [], "status": "stub"},
            meta={"phase": 3},
        )
