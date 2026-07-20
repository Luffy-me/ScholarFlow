"use client";

import { Search } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { useAiStatus } from "@/hooks/use-api";

export function TopNav({ onOpenCommand }: { onOpenCommand: () => void }) {
  const { data: status } = useAiStatus();
  return (
    <header className="flex h-14 items-center justify-between border-b border-[var(--border)] bg-[color-mix(in_oklab,var(--background)_86%,transparent)] px-5 backdrop-blur">
      <div className="text-sm text-[var(--muted-foreground)]">Workspace</div>
      <div className="flex items-center gap-2">
        <Badge tone={status?.online ? "success" : "warning"}>
          {status?.online ? `AI online · ${status.provider}` : status?.detail || "AI offline"}
        </Badge>
        <Button variant="outline" size="sm" onClick={onOpenCommand} aria-label="Open command palette">
          <Search className="h-3.5 w-3.5" />
          Search
          <kbd className="ml-1 rounded bg-[var(--muted)] px-1.5 py-0.5 text-[10px]">⌘K</kbd>
        </Button>
      </div>
    </header>
  );
}
