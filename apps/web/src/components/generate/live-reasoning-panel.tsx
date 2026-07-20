"use client";

import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { ChevronDown, Brain } from "lucide-react";
import type { ReasoningSections } from "@/lib/store";
import { cn } from "@/lib/utils";
import { EmptyState } from "@/components/ui/empty-state";

function Section({
  title,
  items,
  defaultOpen = true,
}: {
  title: string;
  items: string[];
  defaultOpen?: boolean;
}) {
  const [open, setOpen] = useState(defaultOpen);
  if (!items.length) return null;

  return (
    <div className="rounded-xl border border-[var(--border)] overflow-hidden">
      <button
        type="button"
        className="flex w-full items-center justify-between px-3 py-2.5 text-left text-sm font-medium hover:bg-[var(--muted)] transition-colors"
        onClick={() => setOpen((v) => !v)}
        aria-expanded={open}
      >
        {title}
        <ChevronDown className={cn("h-4 w-4 transition-transform", open && "rotate-180")} />
      </button>
      <AnimatePresence initial={false}>
        {open ? (
          <motion.ul
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: "auto", opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            className="border-t border-[var(--border)] px-3 py-2 space-y-1.5 text-sm text-[var(--muted-foreground)]"
          >
            {items.map((item, i) => (
              <li key={i} className="leading-relaxed">
                {item}
              </li>
            ))}
          </motion.ul>
        ) : null}
      </AnimatePresence>
    </div>
  );
}

export function LiveReasoningPanel({ sections }: { sections: ReasoningSections | null }) {
  if (!sections) {
    return (
      <EmptyState
        icon={Brain}
        title="Reasoning in progress"
        description="Assumptions, tradeoffs, and insights appear as reasoning completes."
      />
    );
  }

  const hasContent =
    sections.assumptions.length ||
    sections.contradictions.length ||
    sections.tradeoffs.length ||
    sections.frameworks.length ||
    sections.insights.length;

  if (!hasContent) {
    return (
      <div className="space-y-2 text-sm text-[var(--muted-foreground)]">
        <p>Structured reasoning from the latest generate run.</p>
        <pre className="max-h-48 overflow-auto rounded-xl bg-[var(--muted)] p-2 text-xs">
          {JSON.stringify(sections.meta.selected_angle || sections.meta.strategy, null, 2)}
        </pre>
      </div>
    );
  }

  return (
    <div className="space-y-2 max-h-[420px] overflow-auto sf-scrollbar">
      <Section title="Insights" items={sections.insights} />
      <Section title="Assumptions" items={sections.assumptions} defaultOpen={false} />
      <Section title="Contradictions" items={sections.contradictions} defaultOpen={false} />
      <Section title="Tradeoffs" items={sections.tradeoffs} defaultOpen={false} />
      <Section title="Frameworks" items={sections.frameworks} defaultOpen={false} />
    </div>
  );
}
