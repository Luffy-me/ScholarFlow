"""Phase 3 stub — Trend Research Agent contract."""

from agents.base import Agent, AgentInput, AgentOutput


class TrendAnalyzerAgent(Agent[AgentInput, AgentOutput]):
    name = "trend_analyzer"

    async def run(self, payload: AgentInput) -> AgentOutput:
        return AgentOutput(
            data={
                "topic": payload.topic,
                "trend_level": "",
                "why_it_matters": "",
                "possible_angles": [],
                "target_audience": "",
                "status": "stub",
            },
            meta={"phase": 3},
        )
