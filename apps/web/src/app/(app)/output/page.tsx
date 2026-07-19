"use client";

import dynamic from "next/dynamic";
import { Suspense, useEffect, useMemo, useState } from "react";
import { useSearchParams } from "next/navigation";
import { toast } from "sonner";
import { useEvidence, usePost } from "@/hooks/use-api";
import { useWorkflowStore } from "@/lib/store";
import { api } from "@/lib/api";
import { readingTimeMinutes, wordCount } from "@/lib/utils";
import { Button } from "@/components/ui/button";
import { Card, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { MetricCard } from "@/components/ui/metric-card";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";

const Monaco = dynamic(() => import("@monaco-editor/react"), { ssr: false, loading: () => <Skeleton className="h-[480px]" /> });

function OutputInner() {
  const params = useSearchParams();
  const id = params.get("id") || undefined;
  const { data: post, isLoading } = usePost(id);
  const { data: evidence } = useEvidence(id);
  const { lastGenerate, draftVersions, pushVersion, restoreVersion } = useWorkflowStore();
  const [text, setText] = useState("");

  useEffect(() => {
    if (post?.body) setText(post.body);
    else if (lastGenerate?.final_text) setText(lastGenerate.final_text);
  }, [post, lastGenerate]);

  const scores = useMemo(() => {
    return {
      quality: (post?.critic_scores || lastGenerate?.quality_score || {}) as Record<string, unknown>,
      engagement: (post?.engagement_prediction || lastGenerate?.engagement_prediction || {}) as Record<string, unknown>,
      writing: (lastGenerate?.writing_quality || {}) as Record<string, unknown>,
    };
  }, [post, lastGenerate]);

  async function save() {
    if (!id) {
      pushVersion(text, "Local edit");
      toast.message("Saved locally (no post id)");
      return;
    }
    try {
      await api.updatePost(id, { body: text });
      pushVersion(text, "Saved to backend");
      toast.success("Post updated");
    } catch (e) {
      toast.error(e instanceof Error ? e.message : "Save failed");
    }
  }

  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      if ((e.metaKey || e.ctrlKey) && e.key.toLowerCase() === "s") {
        e.preventDefault();
        void save();
      }
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  });

  if (isLoading && id) return <Skeleton className="h-96" />;

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap items-end justify-between gap-3">
        <div>
          <h1 className="text-2xl font-semibold tracking-tight">Output</h1>
          <p className="text-sm text-[var(--muted-foreground)]">
            {post?.topic || lastGenerate?.topic || "Generated post"}
          </p>
        </div>
        <div className="flex gap-2">
          <Badge>{post?.status || lastGenerate?.status || "draft"}</Badge>
          <Button variant="outline" onClick={() => navigator.clipboard.writeText(text)}>
            Copy
          </Button>
          <Button onClick={save}>Save</Button>
        </div>
      </div>

      <div className="grid gap-4 xl:grid-cols-[1.35fr_0.85fr]">
        <Card className="overflow-hidden p-0">
          <div className="flex items-center justify-between border-b border-[var(--border)] px-4 py-3">
            <div>
              <CardTitle>Generated post</CardTitle>
              <CardDescription>
                {wordCount(text)} words · ~{readingTimeMinutes(text)} min read
              </CardDescription>
            </div>
          </div>
          <div className="h-[560px]">
            <Monaco
              height="100%"
              defaultLanguage="markdown"
              theme="vs"
              value={text}
              onChange={(v) => setText(v || "")}
              options={{
                minimap: { enabled: false },
                fontSize: 14,
                wordWrap: "on",
                lineNumbers: "off",
                padding: { top: 16 },
              }}
            />
          </div>
          <div className="border-t border-[var(--border)] p-4">
            <CardTitle className="mb-2 text-sm">Version history</CardTitle>
            <div className="space-y-2">
              {draftVersions.length ? (
                draftVersions.slice(0, 6).map((v) => (
                  <button
                    key={v.id}
                    className="flex w-full items-center justify-between rounded-xl border border-[var(--border)] px-3 py-2 text-left text-sm hover:bg-[var(--muted)]"
                    onClick={() => {
                      const restored = restoreVersion(v.id);
                      if (restored) setText(restored);
                    }}
                  >
                    <span>{v.label}</span>
                    <span className="text-xs text-[var(--muted-foreground)]">
                      {new Date(v.at).toLocaleString()}
                    </span>
                  </button>
                ))
              ) : (
                <p className="text-sm text-[var(--muted-foreground)]">No versions yet.</p>
              )}
            </div>
          </div>
        </Card>

        <div className="space-y-4">
          <div className="grid grid-cols-2 gap-3">
            <MetricCard label="Hook" value={String(scores.engagement.hook_score ?? "—")} />
            <MetricCard label="Novelty / originality" value={String(scores.quality.originality ?? scores.engagement.originality_score ?? "—")} />
            <MetricCard label="Evidence / truth" value={String(scores.quality.truth ?? scores.quality.evidence ?? "—")} />
            <MetricCard label="Readability / clarity" value={String(scores.quality.clarity ?? scores.writing.human_quality_score ?? "—")} />
            <MetricCard label="LinkedIn / overall" value={String(scores.quality.overall ?? scores.engagement.overall_score ?? "—")} />
            <MetricCard label="Discussion" value={String(scores.engagement.discussion_score ?? scores.quality.discussion_potential ?? "—")} />
          </div>
          <Card>
            <CardHeader>
              <CardTitle>Predicted engagement</CardTitle>
            </CardHeader>
            <pre className="overflow-auto rounded-xl bg-[var(--muted)] p-3 text-xs">
              {JSON.stringify(scores.engagement, null, 2)}
            </pre>
          </Card>
          <Card>
            <CardHeader>
              <CardTitle>Publishing recommendation</CardTitle>
            </CardHeader>
            <CardDescription>
              {lastGenerate?.safe
                ? "Safe to review. Prefer Tue–Thu morning windows for practitioner audiences. Skip hashtag soup."
                : "Resolve grounding warnings before publishing."}
            </CardDescription>
            {lastGenerate?.grounding?.warnings?.length ? (
              <ul className="mt-3 list-disc space-y-1 pl-5 text-sm text-[var(--warning)]">
                {lastGenerate.grounding.warnings.map((w) => (
                  <li key={w}>{w}</li>
                ))}
              </ul>
            ) : null}
          </Card>
          <Card>
            <CardHeader>
              <CardTitle>Evidence</CardTitle>
            </CardHeader>
            {evidence?.length ? (
              <ul className="space-y-2 text-sm">
                {evidence.map((e) => (
                  <li key={e.id} className="rounded-xl bg-[var(--muted)] px-3 py-2">
                    <div className="font-medium">{e.source}</div>
                    <div className="text-[var(--muted-foreground)]">{e.extracted_claim}</div>
                  </li>
                ))}
              </ul>
            ) : (
              <CardDescription>
                {lastGenerate?.research?.evidence?.length
                  ? `${lastGenerate.research.evidence.length} research claims available from the latest generate run.`
                  : "Attach evidence via the posts evidence API after saving."}
              </CardDescription>
            )}
          </Card>
        </div>
      </div>
    </div>
  );
}

export default function OutputPage() {
  return (
    <Suspense fallback={<Skeleton className="h-96 w-full" />}>
      <OutputInner />
    </Suspense>
  );
}
