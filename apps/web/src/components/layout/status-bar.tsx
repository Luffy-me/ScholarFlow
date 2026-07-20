"use client";

import { useAiStatus, usePosts } from "@/hooks/use-api";
import { useWorkflowStore } from "@/lib/store";

export function StatusBar() {
  const { data: status } = useAiStatus();
  const { data: posts } = usePosts();
  const stages = useWorkflowStore((s) => s.stages);
  const running = stages.find((s) => s.status === "running");
  return (
    <footer className="flex h-9 items-center justify-between border-t border-[var(--border)] bg-[var(--card)] px-4 text-[11px] text-[var(--muted-foreground)]">
      <div className="flex items-center gap-3">
        <span>{status?.online ? "Connected" : "Backend / AI unavailable"}</span>
        <span>·</span>
        <span>{posts?.length ?? 0} posts</span>
      </div>
      <div>{running ? `Running: ${running.label}` : "Ready"}</div>
    </footer>
  );
}
