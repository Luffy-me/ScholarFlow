"use client";

import Link from "next/link";
import { useMemo } from "react";
import { ArrowRight, FileText, Sparkles } from "lucide-react";
import { useKnowledgeGraph, useModes, usePosts } from "@/hooks/use-api";
import { useWorkflowStore } from "@/lib/store";
import { Button } from "@/components/ui/button";
import { Card, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { MetricCard } from "@/components/ui/metric-card";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { EmptyState } from "@/components/ui/empty-state";

export default function DashboardPage() {
  const { data: posts, isLoading } = usePosts();
  const { data: modes } = useModes();
  const { data: graph } = useKnowledgeGraph();
  const lastGenerate = useWorkflowStore((s) => s.lastGenerate);

  const recent = useMemo(() => (posts || []).slice(0, 5), [posts]);
  const trends = lastGenerate?.research?.trends || [];
  const opportunity = lastGenerate?.content_opportunity as Record<string, unknown> | undefined;

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-end justify-between gap-4">
        <div>
          <h1 className="text-2xl font-semibold tracking-tight">Dashboard</h1>
          <p className="mt-1 text-sm text-[var(--muted-foreground)]">
            Research, generate, review, and export — one seamless workspace.
          </p>
        </div>
        <Button asChild size="lg">
          <Link href="/generate">
            <Sparkles className="h-4 w-4" />
            Quick Generate
          </Link>
        </Button>
      </div>

      <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
        <MetricCard label="Posts" value={posts?.length ?? 0} hint="Saved generations" />
        <MetricCard label="Knowledge nodes" value={graph?.nodes?.length ?? 0} />
        <MetricCard label="Knowledge edges" value={graph?.edges?.length ?? 0} />
        <MetricCard
          label="Opportunity"
          value={opportunity?.score != null ? String(opportunity.score) : "—"}
          hint={String(opportunity?.recommended_angle || "Run generate for a score")}
        />
      </div>

      <div className="grid gap-4 xl:grid-cols-3">
        <Card className="xl:col-span-2">
          <CardHeader>
            <CardTitle>Latest generated posts</CardTitle>
            <Button asChild variant="ghost" size="sm">
              <Link href="/history">
                History <ArrowRight className="h-3.5 w-3.5" />
              </Link>
            </Button>
          </CardHeader>
          {isLoading ? (
            <div className="space-y-2">
              <Skeleton className="h-14" />
              <Skeleton className="h-14" />
            </div>
          ) : recent.length ? (
            <div className="space-y-2">
              {recent.map((post) => (
                <Link
                  key={post.id}
                  href={`/output?id=${post.id}`}
                  className="block rounded-xl border border-[var(--border)] px-3 py-3 transition hover:bg-[var(--muted)]"
                >
                  <div className="flex items-center justify-between gap-2">
                    <div className="font-medium">{post.topic}</div>
                    <Badge>{post.status}</Badge>
                  </div>
                  <p className="mt-1 line-clamp-2 text-sm text-[var(--muted-foreground)]">{post.body}</p>
                </Link>
              ))}
            </div>
          ) : (
            <div className="px-4 pb-4">
              <EmptyState
                icon={FileText}
                title="Generate your first LinkedIn post."
                description="Evidence-backed drafts appear here after you run Generate."
                action={
                  <Button asChild>
                    <Link href="/generate">
                      <Sparkles className="h-4 w-4" />
                      Start generating
                    </Link>
                  </Button>
                }
              />
            </div>
          )}
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Trending topics</CardTitle>
          </CardHeader>
          {trends.length ? (
            <ul className="space-y-2 text-sm">
              {trends.slice(0, 5).map((t) => (
                <li key={t.trend} className="rounded-xl bg-[var(--muted)] px-3 py-2">
                  <div className="font-medium">{t.trend}</div>
                  <div className="text-xs text-[var(--muted-foreground)]">
                    momentum {t.momentum.toFixed(2)} · confidence {t.confidence.toFixed(2)}
                  </div>
                </li>
              ))}
            </ul>
          ) : (
            <CardDescription>Trends appear after a research-backed generate run.</CardDescription>
          )}
        </Card>
      </div>

      <div className="grid gap-4 md:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle>Today&apos;s research</CardTitle>
          </CardHeader>
          {lastGenerate?.research ? (
            <div className="space-y-2 text-sm">
              <p className="text-[var(--muted-foreground)]">{lastGenerate.research.summary}</p>
              <div className="flex flex-wrap gap-2">
                <Badge tone="accent">{lastGenerate.research.sources?.length || 0} sources</Badge>
                <Badge>{lastGenerate.research.evidence?.length || 0} evidence claims</Badge>
              </div>
              <Button asChild variant="outline" size="sm">
                <Link href="/research">Open research</Link>
              </Button>
            </div>
          ) : (
            <CardDescription>Run Generate to populate research summary and evidence.</CardDescription>
          )}
        </Card>
        <Card>
          <CardHeader>
            <CardTitle>Recommended topics</CardTitle>
          </CardHeader>
          <ul className="space-y-2 text-sm">
            {(modes?.default_mode ? [modes.default_mode] : ["founder"]).map((m) => (
              <li key={m} className="rounded-xl border border-[var(--border)] px-3 py-2">
                Mode: {modes?.modes?.[m]?.label || m}
                <div className="text-xs text-[var(--muted-foreground)]">
                  {modes?.modes?.[m]?.opening_guidance || "Use preferred topics from memory in Settings."}
                </div>
              </li>
            ))}
            <li className="rounded-xl bg-[var(--accent-soft)] px-3 py-2 text-[var(--accent)]">
              Tip: start from a constraint, not a buzzword.
            </li>
          </ul>
        </Card>
      </div>
    </div>
  );
}
