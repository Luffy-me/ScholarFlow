"""Research Intelligence orchestrator — senior-researcher style briefing."""

from __future__ import annotations

from typing import Any

from agents.base import AgentInput, AgentOutput
from agents.research.collector import ResearchCollector
from agents.research.deduplicator import ResearchDeduplicator
from agents.research.evidence_extractor import EvidenceExtractor
from agents.research.schemas import ResearchBrief
from agents.research.source_ranker import SourceRanker
from agents.research.summarizer import ResearchSummarizer
from agents.research.trend_detector import TrendDetector
from knowledge.evidence.store import EvidenceStore
from models.capabilities import Capability


class ResearchOrchestratorInput(AgentInput):
    pass


class ResearchOrchestratorOutput(AgentOutput):
    brief: ResearchBrief | None = None


class ResearchOrchestrator:
    """Compose collector → dedupe → rank → evidence → trends → summary."""

    name = "research_orchestrator"
    capabilities = [Capability.RESEARCH]

    def __init__(
        self,
        *,
        connector_names: list[str] | None = None,
        evidence_store: EvidenceStore | None = None,
    ) -> None:
        self.collector = ResearchCollector(connector_names)
        self.deduplicator = ResearchDeduplicator()
        self.ranker = SourceRanker()
        self.extractor = EvidenceExtractor()
        self.trends = TrendDetector()
        self.summarizer = ResearchSummarizer()
        self.evidence_store = evidence_store or EvidenceStore()

    async def run(self, payload: ResearchOrchestratorInput | AgentInput) -> ResearchOrchestratorOutput:
        topic = payload.topic or "untitled topic"
        docs = await self.collector.collect(topic, limit_per_source=2)
        docs = self.deduplicator.dedupe(docs)
        ranked = self.ranker.rank(docs, query=topic)
        evidence = self.extractor.extract(docs, ranked)
        for claim in evidence:
            self.evidence_store.upsert(claim.model_dump())
        trends = self.trends.detect(docs, topic=topic)
        summary, questions = self.summarizer.summarize(
            topic=topic, ranked=ranked, evidence=evidence, trends=trends
        )
        brief = ResearchBrief(
            topic=topic,
            sources=ranked,
            evidence=evidence,
            trends=trends,
            summary=summary,
            open_questions=questions,
            connector_stats=self.collector.stats(docs),
            offline=True,
        )
        return ResearchOrchestratorOutput(
            text=summary,
            brief=brief,
            data=brief.as_dict(),
            meta={"agent": self.name, "offline": True, "source_count": len(ranked)},
        )

    async def research(self, topic: str, **kwargs: Any) -> ResearchBrief:
        result = await self.run(ResearchOrchestratorInput(topic=topic, **kwargs))
        assert result.brief is not None
        return result.brief
