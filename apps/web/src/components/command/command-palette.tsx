"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { Command } from "cmdk";
import {
  BookOpen,
  FileOutput,
  Layers3,
  Network,
  PenSquare,
  Search,
  Settings,
} from "lucide-react";

const actions = [
  { id: "generate", label: "Generate Post", href: "/generate", icon: PenSquare },
  { id: "carousel", label: "Generate Carousel", href: "/carousel", icon: Layers3 },
  { id: "research", label: "Open Research", href: "/research", icon: BookOpen },
  { id: "knowledge", label: "Search Knowledge", href: "/knowledge", icon: Network },
  { id: "exports", label: "Export", href: "/exports", icon: FileOutput },
  { id: "settings", label: "Settings", href: "/settings", icon: Settings },
];

export function CommandPalette({
  open,
  onOpenChange,
}: {
  open: boolean;
  onOpenChange: (open: boolean) => void;
}) {
  const router = useRouter();
  const [query, setQuery] = useState("");

  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      if ((e.metaKey || e.ctrlKey) && (e.key === "k" || e.key === "/")) {
        e.preventDefault();
        onOpenChange(!open);
      }
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [open, onOpenChange]);

  if (!open) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-start justify-center bg-black/30 p-24 backdrop-blur-sm" role="dialog" aria-modal="true">
      <Command
        className="sf-panel w-full max-w-xl overflow-hidden"
        label="Command palette"
      >
        <div className="flex items-center gap-2 border-b border-[var(--border)] px-3">
          <Search className="h-4 w-4 text-[var(--muted-foreground)]" />
          <Command.Input
            value={query}
            onValueChange={setQuery}
            placeholder="Search research, posts, concepts…"
            className="h-12 w-full bg-transparent text-sm outline-none"
          />
        </div>
        <Command.List className="max-h-80 overflow-auto p-2">
          <Command.Empty className="px-3 py-6 text-sm text-[var(--muted-foreground)]">
            No matches.
          </Command.Empty>
          <Command.Group heading="Actions" className="px-1 text-xs text-[var(--muted-foreground)]">
            {actions.map((action) => {
              const Icon = action.icon;
              return (
                <Command.Item
                  key={action.id}
                  value={action.label}
                  onSelect={() => {
                    onOpenChange(false);
                    router.push(action.href);
                  }}
                  className="flex cursor-pointer items-center gap-2 rounded-lg px-3 py-2 text-sm text-[var(--foreground)] aria-selected:bg-[var(--muted)]"
                >
                  <Icon className="h-4 w-4" />
                  {action.label}
                </Command.Item>
              );
            })}
          </Command.Group>
        </Command.List>
      </Command>
      <button className="absolute inset-0 -z-10 cursor-default" aria-label="Close" onClick={() => onOpenChange(false)} />
    </div>
  );
}
