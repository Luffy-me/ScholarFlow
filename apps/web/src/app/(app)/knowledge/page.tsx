"use client";

import { useMemo, useState } from "react";
import ReactFlow, { Background, Controls, MiniMap, type Edge, type Node } from "reactflow";
import "reactflow/dist/style.css";
import { useEvidenceGraph, useKnowledgeGraph } from "@/hooks/use-api";
import { Card, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { MetricCard } from "@/components/ui/metric-card";

export default function KnowledgePage() {
  const { data: graph, isLoading } = useKnowledgeGraph();
  const { data: evidence } = useEvidenceGraph();
  const [q, setQ] = useState("");

  const filteredNodes = useMemo(() => {
    const nodes = graph?.nodes || [];
    if (!q) return nodes;
    return nodes.filter((n) => n.label.toLowerCase().includes(q.toLowerCase()) || n.type.toLowerCase().includes(q.toLowerCase()));
  }, [graph, q]);

  const flowNodes: Node[] = useMemo(
    () =>
      filteredNodes.slice(0, 60).map((n, i) => ({
        id: n.id,
        data: { label: `${n.label}` },
        position: { x: (i % 6) * 180, y: Math.floor(i / 6) * 110 },
        style: {
          borderRadius: 12,
          border: "1px solid var(--border)",
          background: "var(--card)",
          fontSize: 12,
          padding: 8,
          width: 160,
        },
      })),
    [filteredNodes],
  );

  const flowEdges: Edge[] = useMemo(() => {
    const ids = new Set(flowNodes.map((n) => n.id));
    return (graph?.edges || [])
      .filter((e) => ids.has(e.source) && ids.has(e.target))
      .slice(0, 80)
      .map((e) => ({
        id: e.id,
        source: e.source,
        target: e.target,
        label: e.relation,
        style: { stroke: "var(--accent)" },
      }));
  }, [graph, flowNodes]);

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-semibold tracking-tight">Knowledge</h1>
        <p className="text-sm text-[var(--muted-foreground)]">
          Knowledge graph and evidence graph from local stores (read-only UI adapters).
        </p>
      </div>

      <div className="grid gap-3 md:grid-cols-4">
        <MetricCard label="Nodes" value={graph?.nodes?.length ?? 0} />
        <MetricCard label="Edges" value={graph?.edges?.length ?? 0} />
        <MetricCard label="Evidence claims" value={evidence?.claims?.length ?? 0} />
        <MetricCard label="Filtered concepts" value={filteredNodes.length} />
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Concept search</CardTitle>
        </CardHeader>
        <Input placeholder="Search concepts, topics, tools…" value={q} onChange={(e) => setQ(e.target.value)} />
      </Card>

      <Card className="overflow-hidden p-0">
        <div className="border-b border-[var(--border)] px-4 py-3">
          <CardTitle>Knowledge graph viewer</CardTitle>
          <CardDescription>{isLoading ? "Loading…" : "React Flow visualization"}</CardDescription>
        </div>
        <div className="h-[480px]">
          <ReactFlow nodes={flowNodes} edges={flowEdges} fitView>
            <Background gap={18} size={1} />
            <MiniMap />
            <Controls />
          </ReactFlow>
        </div>
      </Card>

      <div className="grid gap-4 xl:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle>Topic relationships</CardTitle>
          </CardHeader>
          <ul className="space-y-2 text-sm">
            {(graph?.edges || []).slice(0, 12).map((e) => (
              <li key={e.id} className="rounded-xl bg-[var(--muted)] px-3 py-2">
                <span className="font-medium">{e.source}</span>{" "}
                <Badge tone="accent">{e.relation}</Badge>{" "}
                <span className="font-medium">{e.target}</span>
              </li>
            ))}
          </ul>
        </Card>
        <Card>
          <CardHeader>
            <CardTitle>Evidence graph</CardTitle>
          </CardHeader>
          <ul className="space-y-2 text-sm">
            {(evidence?.claims || []).slice(0, 12).map((c, i) => (
              <li key={i} className="rounded-xl border border-[var(--border)] px-3 py-2">
                <div>{String(c.claim || "")}</div>
                <div className="text-xs text-[var(--muted-foreground)]">
                  confidence {String(c.confidence ?? "—")} · verified {String(c.verified ?? false)}
                </div>
              </li>
            ))}
            {!evidence?.claims?.length ? (
              <CardDescription>No evidence claims in local evidence graph yet.</CardDescription>
            ) : null}
          </ul>
        </Card>
      </div>
    </div>
  );
}
