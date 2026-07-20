"use client";

import { motion } from "framer-motion";
import { FileText } from "lucide-react";
import { EmptyState } from "@/components/ui/empty-state";

export function StreamingPost({ paragraphs, streaming }: { paragraphs: string[]; streaming?: boolean }) {
  if (!paragraphs.length) {
    return (
      <EmptyState
        icon={FileText}
        title="Generate your first LinkedIn post."
        description="Your draft reveals paragraph by paragraph as writing completes."
      />
    );
  }

  return (
    <article className="prose prose-sm max-w-none space-y-4 dark:prose-invert">
      {paragraphs.map((p, i) => (
        <motion.p
          key={`${i}-${p.slice(0, 24)}`}
          initial={{ opacity: 0, y: 8 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.28, ease: "easeOut" }}
          className="whitespace-pre-wrap text-[15px] leading-relaxed text-[var(--foreground)]"
        >
          {p}
        </motion.p>
      ))}
      {streaming ? (
        <motion.span
          className="inline-block h-4 w-0.5 bg-[var(--accent)]"
          animate={{ opacity: [1, 0.2, 1] }}
          transition={{ repeat: Infinity, duration: 0.9 }}
          aria-hidden
        />
      ) : null}
    </article>
  );
}
