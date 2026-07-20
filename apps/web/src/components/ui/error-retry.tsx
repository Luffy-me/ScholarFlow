"use client";

import { AlertCircle, RotateCcw } from "lucide-react";
import { Button } from "@/components/ui/button";
import type { PipelineStageId } from "@/types/api";

const STAGE_LABELS: Record<PipelineStageId, string> = {
  research: "Research",
  reasoning: "Reasoning",
  writing: "Writing",
  claim_check: "Claim check",
  humanizer: "Humanizer",
  optimizer: "Optimization",
  editorial: "Editorial review",
  carousel: "Carousel",
  export: "Final export",
};

export function ErrorRetry({
  message,
  stage,
  onRetry,
  busy,
}: {
  message: string;
  stage?: PipelineStageId | null;
  onRetry: () => void;
  busy?: boolean;
}) {
  return (
    <div
      className="flex flex-col gap-3 rounded-2xl border border-[var(--danger)]/30 bg-[var(--danger)]/5 px-4 py-4 sm:flex-row sm:items-center sm:justify-between"
      role="alert"
    >
      <div className="flex gap-3">
        <AlertCircle className="h-5 w-5 shrink-0 text-[var(--danger)]" aria-hidden />
        <div>
          <p className="text-sm font-medium">Something went wrong</p>
          <p className="text-sm text-[var(--muted-foreground)]">{message}</p>
          {stage ? (
            <p className="mt-1 text-xs text-[var(--muted-foreground)]">
              Failed at {STAGE_LABELS[stage]}. Retry resumes from this step when possible.
            </p>
          ) : null}
        </div>
      </div>
      <Button variant="outline" onClick={onRetry} disabled={busy} className="shrink-0">
        <RotateCcw className="h-4 w-4" />
        {busy ? "Retrying…" : "Retry"}
      </Button>
    </div>
  );
}
