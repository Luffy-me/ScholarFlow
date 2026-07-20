"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { Command } from "cmdk";
import {
  BookOpen,
  FileOutput,
  History,
  Layers3,
  Moon,
  Network,
  PenSquare,
  Search,
  Settings,
  Sun,
} from "lucide-react";
import { useWorkflowStore } from "@/lib/store";

const navActions = [
  { id: "generate", label: "Generate", href: "/generate", icon: PenSquare, keywords: "create post" },
  { id: "export", label: "Export", href: "/exports", icon: FileOutput, keywords: "download markdown" },
  { id: "research", label: "Research", href: "/research", icon: BookOpen, keywords: "sources evidence" },
  { id: "history", label: "History", href: "/history", icon: History, keywords: "posts versions" },
  { id: "carousel", label: "Carousel", href: "/carousel", icon: Layers3, keywords: "slides" },
  { id: "knowledge", label: "Knowledge", href: "/knowledge", icon: Network, keywords: "graph" },
  { id: "settings", label: "Settings", href: "/settings", icon: Settings, keywords: "preferences" },
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
  const theme = useWorkflowStore((s) => s.theme);
  const setTheme = useWorkflowStore((s) => s.setTheme);

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

  useEffect(() => {
    if (!open) setQuery("");
  }, [open]);

  if (!open) return null;

  return (
    <div
      className="fixed inset-0 z-50 flex items-start justify-center bg-black/30 p-6 sm:p-24 backdrop-blur-sm"
      role="dialog"
      aria-modal="true"
      onKeyDown={(e) => {
        if (e.key === "Escape") onOpenChange(false);
      }}
    >
      <Command className="sf-panel w-full max-w-xl overflow-hidden shadow-2xl" label="Command palette">
        <div className="flex items-center gap-2 border-b border-[var(--border)] px-3">
          <Search className="h-4 w-4 text-[var(--muted-foreground)]" />
          <Command.Input
            value={query}
            onValueChange={setQuery}
            placeholder="Generate, export, research, history, theme…"
            className="h-12 w-full bg-transparent text-sm outline-none"
          />
        </div>
        <Command.List className="max-h-80 overflow-auto p-2">
          <Command.Empty className="px-3 py-6 text-sm text-[var(--muted-foreground)]">No matches.</Command.Empty>
          <Command.Group heading="Actions" className="px-1 text-xs text-[var(--muted-foreground)]">
            {navActions.map((action) => {
              const Icon = action.icon;
              return (
                <Command.Item
                  key={action.id}
                  value={`${action.label} ${action.keywords}`}
                  onSelect={() => {
                    onOpenChange(false);
                    router.push(action.href);
                  }}
                  className="flex cursor-pointer items-center gap-2 rounded-lg px-3 py-2 text-sm aria-selected:bg-[var(--muted)] transition-colors"
                >
                  <Icon className="h-4 w-4" />
                  {action.label}
                </Command.Item>
              );
            })}
          </Command.Group>
          <Command.Group heading="Theme" className="px-1 pt-2 text-xs text-[var(--muted-foreground)]">
            {(
              [
                { id: "light", label: "Light mode", icon: Sun },
                { id: "dark", label: "Dark mode", icon: Moon },
                { id: "system", label: "System theme", icon: Settings },
              ] as const
            ).map((t) => {
              const Icon = t.icon;
              return (
                <Command.Item
                  key={t.id}
                  value={`theme ${t.label}`}
                  onSelect={() => {
                    setTheme(t.id);
                    onOpenChange(false);
                  }}
                  className="flex cursor-pointer items-center justify-between gap-2 rounded-lg px-3 py-2 text-sm aria-selected:bg-[var(--muted)]"
                >
                  <span className="flex items-center gap-2">
                    <Icon className="h-4 w-4" />
                    {t.label}
                  </span>
                  {theme === t.id ? <span className="text-xs text-[var(--accent)]">Active</span> : null}
                </Command.Item>
              );
            })}
          </Command.Group>
        </Command.List>
      </Command>
      <button
        type="button"
        className="absolute inset-0 -z-10 cursor-default"
        aria-label="Close"
        onClick={() => onOpenChange(false)}
      />
    </div>
  );
}
