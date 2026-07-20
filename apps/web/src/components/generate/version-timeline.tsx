"use client";

import { useMemo, useState } from "react";
import { cn } from "@/lib/utils";
import { Button } from "@/components/ui/button";

export function VersionTimeline({
  versions,
  onSelect,
}: {
  versions: Array<{ id: string; label: string; text: string; at: string }>;
  onSelect?: (text: string) => void;
}) {
  const [leftId, setLeftId] = useState<string>("final");
  const [rightId, setRightId] = useState<string>("v1");

  const left = useMemo(() => versions.find((v) => v.id === leftId)?.text ?? "", [versions, leftId]);
  const right = useMemo(() => versions.find((v) => v.id === rightId)?.text ?? "", [versions, rightId]);

  if (!versions.length) {
    return (
      <p className="text-sm text-[var(--muted-foreground)]">
        v1 → Optimization → Editorial → Final appear after generation.
      </p>
    );
  }

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap items-center gap-2">
        {versions.map((v, i) => (
          <div key={v.id} className="flex items-center gap-2">
            <button
              type="button"
              onClick={() => {
                setLeftId(v.id);
                onSelect?.(v.text);
              }}
              className={cn(
                "rounded-full border px-3 py-1 text-xs font-medium transition-colors hover:bg-[var(--muted)] focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[var(--accent)]",
                leftId === v.id ? "border-[var(--accent)] bg-[var(--accent-soft)]" : "border-[var(--border)]",
              )}
            >
              {v.label}
            </button>
            {i < versions.length - 1 ? (
              <span className="text-[var(--muted-foreground)]" aria-hidden>
                ↓
              </span>
            ) : null}
          </div>
        ))}
      </div>
      <div className="flex flex-wrap gap-2">
        <Button size="sm" variant="outline" onClick={() => setRightId(leftId)}>
          Compare left: {versions.find((v) => v.id === leftId)?.label}
        </Button>
        <select
          className="h-9 rounded-xl border border-[var(--border)] bg-[var(--card)] px-2 text-xs"
          value={rightId}
          onChange={(e) => setRightId(e.target.value)}
          aria-label="Compare with version"
        >
          {versions.map((v) => (
            <option key={v.id} value={v.id}>
              {v.label}
            </option>
          ))}
        </select>
      </div>
      <div className="grid gap-3 md:grid-cols-2">
        <pre className="max-h-64 overflow-auto rounded-xl border border-[var(--border)] bg-[var(--muted)] p-3 text-xs whitespace-pre-wrap">
          {left || "—"}
        </pre>
        <pre className="max-h-64 overflow-auto rounded-xl border border-[var(--border)] bg-[var(--muted)] p-3 text-xs whitespace-pre-wrap">
          {right || "—"}
        </pre>
      </div>
    </div>
  );
}
