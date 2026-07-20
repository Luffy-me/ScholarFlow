"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  BookOpen,
  FileOutput,
  History,
  Home,
  Layers3,
  Network,
  PenSquare,
  Settings,
  Sparkles,
} from "lucide-react";
import { cn } from "@/lib/utils";

const items = [
  { href: "/", label: "Dashboard", icon: Home },
  { href: "/research", label: "Research", icon: BookOpen },
  { href: "/knowledge", label: "Knowledge", icon: Network },
  { href: "/generate", label: "Generate", icon: PenSquare },
  { href: "/carousel", label: "Carousel", icon: Layers3 },
  { href: "/history", label: "History", icon: History },
  { href: "/exports", label: "Exports", icon: FileOutput },
  { href: "/settings", label: "Settings", icon: Settings },
];

export function Sidebar() {
  const pathname = usePathname();
  return (
    <aside className="flex h-full w-[240px] shrink-0 flex-col border-r border-[var(--sidebar-border)] bg-[var(--sidebar)]">
      <div className="flex items-center gap-2 px-5 py-5">
        <div className="flex h-8 w-8 items-center justify-center rounded-xl bg-[var(--accent)] text-white">
          <Sparkles className="h-4 w-4" />
        </div>
        <div>
          <div className="text-sm font-semibold tracking-tight">ScholarFlow</div>
          <div className="text-[11px] text-[var(--muted-foreground)]">Intelligence Studio</div>
        </div>
      </div>
      <nav className="flex-1 space-y-1 px-3 pb-4" aria-label="Primary">
        {items.map((item) => {
          const active = item.href === "/" ? pathname === "/" : pathname.startsWith(item.href);
          const Icon = item.icon;
          return (
            <Link
              key={item.href}
              href={item.href}
              className={cn(
                "flex items-center gap-2.5 rounded-xl px-3 py-2.5 text-sm transition",
                active
                  ? "bg-[var(--accent-soft)] font-medium text-[var(--accent)]"
                  : "text-[var(--muted-foreground)] hover:bg-[var(--muted)] hover:text-[var(--foreground)]",
              )}
              aria-current={active ? "page" : undefined}
            >
              <Icon className="h-4 w-4" />
              {item.label}
            </Link>
          );
        })}
      </nav>
      <div className="border-t border-[var(--sidebar-border)] p-4 text-xs text-[var(--muted-foreground)]">
        Local-first · Evidence-backed
      </div>
    </aside>
  );
}
