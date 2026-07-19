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

export default function HistoryPage() {
  const { data: posts, isLoading } = usePosts();
  const { draftVersions, restoreVersion } = useWorkflowStore();
  const [q, setQ] = useState("");
  const [left, setLeft] = useState<string>("");
  const [right, setRight] = useState<string>("");

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
          <Skeleton className="h-32" />
        ) : (
          <div className="space-y-2">
            {filtered.map((p) => (
              <div key={p.id} className="rounded-xl border border-[var(--border)] px-3 py-3">
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
            ))}
            {!filtered.length ? <CardDescription>No posts found.</CardDescription> : null}
          </div>
        )}
      </Card>

      <div className="grid gap-4 xl:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle>Version history</CardTitle>
          </CardHeader>
          <div className="space-y-2">
            {draftVersions.map((v) => (
              <div key={v.id} className="flex items-center justify-between rounded-xl bg-[var(--muted)] px-3 py-2 text-sm">
                <button className="text-left" onClick={() => setLeft(v.text)}>
                  <div className="font-medium">{v.label}</div>
                  <div className="text-xs text-[var(--muted-foreground)]">{new Date(v.at).toLocaleString()}</div>
                </button>
                <div className="flex gap-2">
                  <Button size="sm" variant="outline" onClick={() => setRight(v.text)}>
                    Compare
                  </Button>
                  <Button
                    size="sm"
                    onClick={() => {
                      restoreVersion(v.id);
                      setLeft(v.text);
                    }}
                  >
                    Restore
                  </Button>
                </div>
              </div>
            ))}
            {!draftVersions.length ? <CardDescription>Local versions appear after generate/save.</CardDescription> : null}
          </div>
        </Card>
        <Card>
          <CardHeader>
            <CardTitle>Compare versions</CardTitle>
          </CardHeader>
          <div className="grid gap-3 md:grid-cols-2">
            <pre className="max-h-80 overflow-auto rounded-xl bg-[var(--muted)] p-3 text-xs whitespace-pre-wrap">{left || "Select a version"}</pre>
            <pre className="max-h-80 overflow-auto rounded-xl bg-[var(--muted)] p-3 text-xs whitespace-pre-wrap">{right || "Select compare target"}</pre>
          </div>
        </Card>
      </div>
    </div>
  );
}
