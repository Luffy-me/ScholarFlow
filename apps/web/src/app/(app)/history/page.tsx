"use client";

import Link from "next/link";
import { useMemo, useState } from "react";
import { usePosts } from "@/hooks/use-api";
import { useWorkflowStore } from "@/lib/store";
import { Card, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { VirtualList } from "@/components/ui/virtual-list";
import { VersionTimeline } from "@/components/generate/version-timeline";
import { EmptyState } from "@/components/ui/empty-state";
import { History } from "lucide-react";

export default function HistoryPage() {
  const { data: posts, isLoading } = usePosts();
  const { draftVersions, restoreVersion, versionTimeline } = useWorkflowStore();
  const [q, setQ] = useState("");

  const filtered = useMemo(() => {
    const list = posts || [];
    if (!q) return list;
    return list.filter((p) => `${p.topic} ${p.body}`.toLowerCase().includes(q.toLowerCase()));
  }, [posts, q]);

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-semibold tracking-tight">History</h1>
        <p className="text-sm text-[var(--muted-foreground)]">Generated posts, versions, compare & restore.</p>
      </div>

      <Card>
        <Input placeholder="Search posts…" value={q} onChange={(e) => setQ(e.target.value)} />
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Generated posts</CardTitle>
        </CardHeader>
        {isLoading ? (
          <Skeleton className="m-4 h-32" />
        ) : filtered.length ? (
          <VirtualList
            items={filtered}
            estimateSize={108}
            className="max-h-[520px] overflow-auto sf-scrollbar px-2 pb-2"
            renderItem={(p) => (
              <div className="mb-2 rounded-xl border border-[var(--border)] px-3 py-3 transition-colors hover:bg-[var(--muted)]/50">
                <div className="flex flex-wrap items-center justify-between gap-2">
                  <div className="font-medium">{p.topic}</div>
                  <div className="flex items-center gap-2">
                    <Badge>{p.status}</Badge>
                    <Button asChild size="sm" variant="outline">
                      <Link href={`/output?id=${p.id}`}>Open</Link>
                    </Button>
                  </div>
                </div>
                <p className="mt-1 line-clamp-2 text-sm text-[var(--muted-foreground)]">{p.body}</p>
                <div className="mt-2 text-xs text-[var(--muted-foreground)]">
                  {p.created_at ? new Date(p.created_at).toLocaleString() : "—"} · {p.content_mode} · {p.format}
                </div>
              </div>
            )}
          />
        ) : (
          <div className="p-4">
            <EmptyState
              icon={History}
              title="No posts found."
              description="Generate your first LinkedIn post to build history."
            />
          </div>
        )}
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Pipeline version timeline</CardTitle>
          <CardDescription>v1 → Optimization → Editorial → Final from the latest run.</CardDescription>
        </CardHeader>
        <div className="px-4 pb-4">
          <VersionTimeline versions={versionTimeline} />
        </div>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Local version history</CardTitle>
        </CardHeader>
        <div className="space-y-2 px-4 pb-4">
          {draftVersions.map((v) => (
            <div key={v.id} className="flex items-center justify-between rounded-xl bg-[var(--muted)] px-3 py-2 text-sm">
              <div>
                <div className="font-medium">{v.label}</div>
                <div className="text-xs text-[var(--muted-foreground)]">{new Date(v.at).toLocaleString()}</div>
              </div>
              <Button
                size="sm"
                onClick={() => {
                  restoreVersion(v.id);
                }}
              >
                Restore
              </Button>
            </div>
          ))}
          {!draftVersions.length ? <CardDescription>Local versions appear after generate/save.</CardDescription> : null}
        </div>
      </Card>
    </div>
  );
}
