"use client";

import { useWorkflowStore } from "@/lib/store";
import { Card, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";

export function InspectorPanel() {
  const { inspectorOpen, lastGenerate } = useWorkflowStore();
  if (!inspectorOpen) return null;

  const scores = (lastGenerate?.quality_score || {}) as Record<string, unknown>;
  const engagement = (lastGenerate?.engagement_prediction || {}) as Record<string, unknown>;
  const opportunity = (lastGenerate?.content_opportunity || {}) as Record<string, unknown>;

  return (
    <aside className="hidden w-[300px] shrink-0 border-l border-[var(--border)] bg-[var(--card)] xl:flex xl:flex-col">
      <div className="border-b border-[var(--border)] px-4 py-3 text-sm font-semibold">Inspector</div>
      <div className="sf-scrollbar flex-1 space-y-3 overflow-auto p-4">
        {!lastGenerate ? (
          <p className="text-sm text-[var(--muted-foreground)]">
            Generate a post to inspect scores, evidence, and opportunity signals.
          </p>
        ) : (
          <>
            <Card className="p-3">
              <CardHeader className="mb-2">
                <CardTitle>Latest run</CardTitle>
                <Badge tone={lastGenerate.safe ? "success" : "danger"}>
                  {lastGenerate.status}
                </Badge>
              </CardHeader>
              <CardDescription className="line-clamp-3">{lastGenerate.topic}</CardDescription>
            </Card>
            <Card className="p-3">
              <CardTitle className="mb-2">Quality</CardTitle>
              <div className="space-y-1 text-xs text-[var(--muted-foreground)]">
                <div>Overall: {String(scores.overall ?? "—")}</div>
                <div>Originality: {String(scores.originality ?? "—")}</div>
                <div>Specificity: {String(scores.specificity ?? "—")}</div>
              </div>
            </Card>
            <Card className="p-3">
              <CardTitle className="mb-2">Engagement</CardTitle>
              <div className="space-y-1 text-xs text-[var(--muted-foreground)]">
                <div>Overall: {String(engagement.overall_score ?? "—")}</div>
                <div>Hook: {String(engagement.hook_score ?? "—")}</div>
                <div>Discussion: {String(engagement.discussion_score ?? "—")}</div>
              </div>
            </Card>
            <Card className="p-3">
              <CardTitle className="mb-2">Opportunity</CardTitle>
              <div className="space-y-1 text-xs text-[var(--muted-foreground)]">
                <div>Score: {String(opportunity.score ?? "—")}</div>
                <div className="line-clamp-4">{String(opportunity.reason ?? "—")}</div>
              </div>
            </Card>
          </>
        )}
      </div>
    </aside>
  );
}
