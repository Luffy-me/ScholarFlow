"use client";

import { useAiStatus, usePosts } from "@/hooks/use-api";
import { aiConnected, primaryAiIssue } from "@/lib/ai-status";
import { useWorkflowStore } from "@/lib/store";

export function StatusBar() {
  const { data: status, isError, isLoading } = useAiStatus();
  const { data: posts } = usePosts();
  const stages = useWorkflowStore((s) => s.stages);
  const running = stages.find((s) => s.status === "running");
  const connected = aiConnected(status);
  const issue = primaryAiIssue(status);

  let aiLabel = "Checking AI…";
  if (isError) aiLabel = "API offline — start uvicorn on :8000";
  else if (!isLoading && status) {
    aiLabel = connected ? "✓ Ollama connected" : `✗ ${issue?.message || "Ollama offline"}`;
  }

  return (
    <footer className="flex h-9 items-center justify-between border-t border-[var(--border)] bg-[var(--card)] px-4 text-[11px] text-[var(--muted-foreground)]">
      <div className="flex items-center gap-3 min-w-0">
        <span className="truncate">{aiLabel}</span>
        <span>·</span>
        <span>{posts?.length ?? 0} posts</span>
      </div>
      <div>{running ? `Running: ${running.label}` : "Ready"}</div>
    </footer>
  );
}
