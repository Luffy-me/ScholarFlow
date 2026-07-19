"""Phase 3 stub — Research Agent contract."""

from agents.base import Agent, AgentInput, AgentOutput


class ResearcherAgent(Agent[AgentInput, AgentOutput]):
    name = "researcher"

    async def run(self, payload: AgentInput) -> AgentOutput:
        return AgentOutput(
            data={
                "topic": payload.topic,
                "key_findings": [],
                "sources": [],
                "open_questions": [],
                "status": "stub",
            },
            meta={"phase": 3},
        )
