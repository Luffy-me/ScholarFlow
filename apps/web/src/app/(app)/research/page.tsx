"use client";

import { useMemo, useState } from "react";
import { useWorkflowStore } from "@/lib/store";
import { useEvidenceGraph, useKnowledgeGraph, usePosts } from "@/hooks/use-api";
import { Card, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { MetricCard } from "@/components/ui/metric-card";

export default function ResearchPage() {
  const [q, setQ] = useState("");
  const [tier, setTier] = useState<"all" | "1" | "2" | "3">("all");
  const lastGenerate = useWorkflowStore((s) => s.lastGenerate);
  const research = lastGenerate?.research;
  const { data: posts } = usePosts();
  const { data: graph } = useKnowledgeGraph();
  const { data: evidenceGraph } = useEvidenceGraph();

  const sources = useMemo(() => {
    const list = research?.sources || [];
    return list.filter((s) => {
      const hay = `${s.title} ${s.snippet || ""} ${s.source_type || ""}`.toLowerCase();
      const okQ = !q || hay.includes(q.toLowerCase());
      const okTier = tier === "all" || String(s.tier) === tier;
      return okQ && okTier;
    });
  }, [research, q, tier]);

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-semibold tracking-tight">Research</h1>
        <p className="text-sm text-[var(--muted-foreground)]">
          Sources, evidence, and opportunity signals from the backend generate pipeline.
        </p>
      </div>

      <div className="grid gap-3 md:grid-cols-4">
        <MetricCard label="Sources" value={research?.sources?.length ?? 0} />
        <MetricCard label="Evidence claims" value={research?.evidence?.length ?? 0} />
        <MetricCard
          label="Opportunity"
          value={String((lastGenerate?.content_opportunity as Record<string, unknown> | undefined)?.score ?? "—")}
        />
        <MetricCard label="Graph nodes" value={graph?.nodes?.length ?? 0} />
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Search research</CardTitle>
        </CardHeader>
        <div className="flex flex-wrap gap-3">
          <Input
            className="max-w-md"
            placeholder="Filter sources…"
            value={q}
            onChange={(e) => setQ(e.target.value)}
          />
          <select
            className="h-10 rounded-xl border border-[var(--border)] bg-[var(--card)] px-3 text-sm"
            value={tier}
            onChange={(e) => setTier(e.target.value as typeof tier)}
          >
            <option value="all">All tiers</option>
            <option value="1">Tier 1</option>
            <option value="2">Tier 2</option>
            <option value="3">Tier 3</option>
          </select>
        </div>
      </Card>

      <div className="grid gap-4 xl:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle>Topic summary</CardTitle>
          </CardHeader>
          {research ? (
            <div className="space-y-3 text-sm">
              <p>{research.summary}</p>
              <div className="flex flex-wrap gap-2">
                {(research.key_findings || []).slice(0, 4).map((f) => (
                  <Badge key={f} tone="accent">
                    {f}
                  </Badge>
                ))}
              </div>
              <div>
                <div className="mb-1 font-medium">Open questions</div>
                <ul className="list-disc space-y-1 pl-5 text-[var(--muted-foreground)]">
                  {(research.open_questions || []).map((qItem) => (
                    <li key={qItem}>{qItem}</li>
                  ))}
                </ul>
              </div>
            </div>
          ) : (
            <CardDescription>Generate a topic to load research summary from `/api/v1/generate`.</CardDescription>
          )}
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Reasoning / insight</CardTitle>
          </CardHeader>
          {lastGenerate?.insight ? (
            <pre className="overflow-auto rounded-xl bg-[var(--muted)] p-3 text-xs">
              {JSON.stringify(lastGenerate.insight, null, 2)}
            </pre>
          ) : (
            <CardDescription>Insight engine output appears after generation.</CardDescription>
          )}
        </Card>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Sources</CardTitle>
          <CardDescription>{sources.length} matching</CardDescription>
        </CardHeader>
        <div className="space-y-2">
          {sources.map((s, idx) => (
            <a
              key={`${s.id || s.url || s.title}-${idx}`}
              href={s.url || undefined}
              target="_blank"
              rel="noreferrer"
              className="block rounded-xl border border-[var(--border)] px-3 py-3 transition hover:bg-[var(--muted)]"
            >
              <div className="flex items-center justify-between gap-2">
                <div className="font-medium">{s.title}</div>
                <Badge>tier {s.tier}</Badge>
              </div>
              <div className="mt-1 text-xs text-[var(--muted-foreground)]">
                {s.source_type} {s.url ? `· ${s.url}` : ""}
              </div>
              <p className="mt-1 text-sm text-[var(--muted-foreground)]">{s.snippet}</p>
            </a>
          ))}
          {!sources.length ? (
            <CardDescription>No sources yet. Run Generate to populate research sources.</CardDescription>
          ) : null}
        </div>
      </Card>

      <div className="grid gap-4 xl:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle>Evidence</CardTitle>
          </CardHeader>
          <div className="space-y-2">
            {(research?.evidence || evidenceGraph?.claims || []).slice(0, 12).map((e, i) => {
              const claim = "claim" in e ? String(e.claim) : JSON.stringify(e);
              const conf = "confidence" in e ? Number(e.confidence) : null;
              return (
                <div key={i} className="rounded-xl bg-[var(--muted)] px-3 py-2 text-sm">
                  <div>{claim}</div>
                  {conf != null ? (
                    <div className="text-xs text-[var(--muted-foreground)]">confidence {conf}</div>
                  ) : null}
                </div>
              );
            })}
          </div>
        </Card>
        <Card>
          <CardHeader>
            <CardTitle>Recent saved posts</CardTitle>
          </CardHeader>
          <ul className="space-y-2 text-sm">
            {(posts || []).slice(0, 6).map((p) => (
              <li key={p.id} className="rounded-xl border border-[var(--border)] px-3 py-2">
                {p.topic}
              </li>
            ))}
          </ul>
        </Card>
      </div>
    </div>
  );
}
