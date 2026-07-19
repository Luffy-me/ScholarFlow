# Knowledge Graph

Local-first JSON graph: `knowledge_graph/graph.json`

## Node types

- Topic
- Tool
- Company
- Technology
- ResearchPaper
- Person
- Concept

## Relationships

- supports
- contradicts
- depends_on
- compares_to
- extends
- supersedes

## API

```python
from knowledge_graph import KnowledgeGraph, NodeType, RelationType

graph = KnowledgeGraph()
topic = graph.upsert_node(NodeType.TOPIC, "RAG evaluation")
tool = graph.upsert_node(NodeType.TOOL, "Ollama")
graph.add_edge(topic.id, tool.id, RelationType.DEPENDS_ON)
```

The generation pipeline links the active topic to top research source labels automatically.

## Evidence vs knowledge graph

| Store | Purpose |
|---|---|
| `knowledge/evidence/` | Claim ↔ sources truth layer for writing |
| `knowledge_graph/` | Conceptual relationships across topics/tools/papers |
