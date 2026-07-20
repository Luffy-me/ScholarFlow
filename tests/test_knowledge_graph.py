"""Knowledge graph tests."""

from __future__ import annotations

from knowledge_graph import KnowledgeGraph, NodeType, RelationType


def test_knowledge_graph_nodes_and_relationships(tmp_path) -> None:
    graph = KnowledgeGraph(tmp_path / "graph.json")
    topic = graph.upsert_node(NodeType.TOPIC, "local evaluation loops")
    tool = graph.upsert_node(NodeType.TOOL, "Ollama")
    paper = graph.upsert_node(NodeType.RESEARCH_PAPER, "Eval Harness Notes")
    edge1 = graph.add_edge(topic.id, tool.id, RelationType.DEPENDS_ON)
    edge2 = graph.add_edge(paper.id, topic.id, RelationType.SUPPORTS)
    edge3 = graph.add_edge(tool.id, paper.id, RelationType.COMPARES_TO)

    assert len(graph.nodes()) == 3
    assert len(graph.edges()) == 3
    rels = graph.relationships_for(topic.id)
    assert {edge1.id, edge2.id} <= {r["id"] for r in rels}
    assert edge3.relation == RelationType.COMPARES_TO


def test_knowledge_graph_contradicts_and_supersedes(tmp_path) -> None:
    graph = KnowledgeGraph(tmp_path / "g2.json")
    a = graph.upsert_node(NodeType.CONCEPT, "Bigger models always win")
    b = graph.upsert_node(NodeType.CONCEPT, "Evaluation loops dominate quality")
    c = graph.upsert_node(NodeType.TECHNOLOGY, "Qwen3")
    d = graph.upsert_node(NodeType.TECHNOLOGY, "Qwen3.5")
    graph.add_edge(b.id, a.id, RelationType.CONTRADICTS)
    graph.add_edge(d.id, c.id, RelationType.SUPERSEDES)
    graph.add_edge(b.id, a.id, RelationType.EXTENDS)  # same endpoints different relation ids

    relations = {e["relation"] for e in graph.edges()}
    assert "contradicts" in relations
    assert "supersedes" in relations
    assert "extends" in relations


def test_link_topic_to_sources(tmp_path) -> None:
    graph = KnowledgeGraph(tmp_path / "g3.json")
    graph.link_topic_to_sources("RAG", ["chunking", "retrieval quality"])
    assert any(n["type"] == "Topic" for n in graph.nodes())
    assert len(graph.edges()) >= 2
