"use client";

import { Check, Circle, Loader2 } from "lucide-react";
import type { PipelineStageState } from "@/types/api";
import { cn, formatDuration } from "@/lib/utils";

export function PipelineStepper({ stages }: { stages: PipelineStageState[] }) {
  return (
    <ol className="space-y-2" aria-label="Generation pipeline">
      {stages.map((stage) => (
        <li
          key={stage.id}
          className={cn(
            "flex items-center justify-between rounded-xl border border-[var(--border)] px-3 py-2.5 text-sm",
            stage.status === "running" && "border-[var(--accent)] bg-[var(--accent-soft)]",
            stage.status === "completed" && "bg-[var(--card)]",
          )}
        >
          <div className="flex items-center gap-2">
            {stage.status === "running" ? (
              <Loader2 className="h-4 w-4 animate-spin text-[var(--accent)]" />
            ) : stage.status === "completed" ? (
              <Check className="h-4 w-4 text-[var(--success)]" />
            ) : (
              <Circle className="h-4 w-4 text-[var(--muted-foreground)]" />
            )}
            <span className="font-medium">{stage.label}</span>
          </div>
          <div className="text-xs text-[var(--muted-foreground)]">
            {stage.status === "completed" && stage.ms != null
              ? formatDuration(stage.ms)
              : stage.status === "running"
                ? "Running"
                : stage.status === "skipped"
                  ? "Skipped"
                  : "Pending"}
          </div>
        </li>
      ))}
    </ol>
  );
}
