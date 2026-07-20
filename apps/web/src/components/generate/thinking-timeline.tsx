"use client";

import { motion } from "framer-motion";
import { Check } from "lucide-react";
import { format } from "date-fns";
import type { TimelineEvent } from "@/lib/store";
import { cn } from "@/lib/utils";

export function ThinkingTimeline({ events }: { events: TimelineEvent[] }) {
  if (!events.length) {
    return (
      <p className="text-sm text-[var(--muted-foreground)]">
        Milestones appear as each stage completes.
      </p>
    );
  }

  return (
    <ol className="relative space-y-0 border-l border-[var(--border)] pl-4" aria-label="Thinking timeline">
      {events.map((event, i) => (
        <motion.li
          key={event.id}
          initial={{ opacity: 0, x: -4 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ duration: 0.2, delay: i * 0.02 }}
          className="relative pb-4 last:pb-0"
        >
          <span
            className={cn(
              "absolute -left-[1.35rem] flex h-5 w-5 items-center justify-center rounded-full border border-[var(--border)] bg-[var(--card)]",
            )}
            aria-hidden
          >
            <Check className="h-3 w-3 text-[var(--success)]" />
          </span>
          <div className="text-sm font-medium">{event.label}</div>
          <time className="text-xs text-[var(--muted-foreground)]" dateTime={event.at}>
            {format(new Date(event.at), "HH:mm:ss.SSS")}
          </time>
        </motion.li>
      ))}
    </ol>
  );
}
