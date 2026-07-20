"use client";

import { Search } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { useAiStatus } from "@/hooks/use-api";
import { aiConnected, primaryAiIssue } from "@/lib/ai-status";

export function TopNav({ onOpenCommand }: { onOpenCommand: () => void }) {
  const { data: status, isError } = useAiStatus();
  const connected = aiConnected(status);
  const issue = primaryAiIssue(status);

  return (
    <header className="flex h-14 items-center justify-between border-b border-[var(--border)] bg-[color-mix(in_oklab,var(--background)_86%,transparent)] px-5 backdrop-blur">
      <div className="text-sm text-[var(--muted-foreground)]">Workspace</div>
      <div className="flex items-center gap-2">
        <Badge tone={isError ? "danger" : connected ? "success" : "warning"}>
          {isError
            ? "API offline"
            : connected
              ? `✓ Connected · ${status?.writer}`
              : `✗ Offline`}
        </Badge>
        <Button variant="outline" size="sm" onClick={onOpenCommand} aria-label="Open command palette">
          <Search className="h-3.5 w-3.5" />
          Search
          <kbd className="ml-1 rounded bg-[var(--muted)] px-1.5 py-0.5 text-[10px]">⌘K</kbd>
        </Button>
      </div>
      {!isError && !connected && issue?.resolution ? (
        <span className="sr-only">{issue.resolution}</span>
      ) : null}
    </header>
  );
}
