"use client";

import { motion } from "framer-motion";
import { BookOpen } from "lucide-react";
import type { ResearchEvidence, ResearchSource } from "@/types/api";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { EmptyState } from "@/components/ui/empty-state";

export function LiveResearchPanel({
  sources,
  evidence,
  summary,
  loading,
}: {
  sources: ResearchSource[];
  evidence: ResearchEvidence[];
  summary: string;
  loading?: boolean;
}) {
  const empty = !sources.length && !evidence.length && !summary;

  if (loading && empty) {
    return (
      <div className="space-y-2" aria-busy>
        <Skeleton className="h-12" />
        <Skeleton className="h-12" />
        <Skeleton className="h-20" />
      </div>
    );
  }

  if (empty) {
    return (
      <EmptyState
        icon={BookOpen}
        title="No research yet."
        description="Sources, evidence, and summary stream in as research completes."
      />
    );
  }

  return (
    <div className="space-y-3 max-h-[420px] overflow-auto sf-scrollbar">
      {sources.map((s, i) => (
        <motion.div
          key={s.url || s.title || i}
          initial={{ opacity: 0, y: 6 }}
          animate={{ opacity: 1, y: 0 }}
          className="rounded-xl border border-[var(--border)] px-3 py-2.5 text-sm"
        >
          <div className="flex items-start justify-between gap-2">
            <div className="font-medium leading-snug">{s.title}</div>
            <Badge tone="accent">Tier {s.tier}</Badge>
          </div>
          {s.snippet ? (
            <p className="mt-1 text-xs text-[var(--muted-foreground)] line-clamp-2">{s.snippet}</p>
          ) : null}
          <div className="mt-1 text-[10px] text-[var(--muted-foreground)] truncate">{s.url}</div>
        </motion.div>
      ))}
      {evidence.map((e, i) => (
        <motion.div
          key={`${e.claim}-${i}`}
          initial={{ opacity: 0, y: 6 }}
          animate={{ opacity: 1, y: 0 }}
          className="rounded-xl bg-[var(--muted)] px-3 py-2.5 text-sm"
        >
          <div className="text-xs font-medium uppercase tracking-wide text-[var(--muted-foreground)]">
            Evidence
          </div>
          <p className="mt-1">{e.claim}</p>
          <div className="mt-2 flex flex-wrap gap-2 text-xs text-[var(--muted-foreground)]">
            <span>Confidence {(e.confidence * 100).toFixed(0)}%</span>
            {e.verified ? <Badge tone="success">Verified</Badge> : null}
          </div>
        </motion.div>
      ))}
      {summary ? (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          className="rounded-xl border border-dashed border-[var(--border)] px-3 py-2.5 text-sm"
        >
          <div className="text-xs font-medium uppercase tracking-wide text-[var(--muted-foreground)]">
            Summary
          </div>
          <p className="mt-1 text-[var(--foreground)]">{summary}</p>
        </motion.div>
      ) : null}
    </div>
  );
}
