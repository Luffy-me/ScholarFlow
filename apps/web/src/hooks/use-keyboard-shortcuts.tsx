"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { useWorkflowStore } from "@/lib/store";
import { registerExportShortcuts } from "@/components/export/export-actions";

export function KeyboardShortcutsProvider({
  commandOpen,
  setCommandOpen,
}: {
  commandOpen: boolean;
  setCommandOpen: (open: boolean) => void;
}) {
  const router = useRouter();
  const lastGenerate = useWorkflowStore((s) => s.lastGenerate);

  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      if (e.key === "Escape") {
        setCommandOpen(false);
      }
      if ((e.metaKey || e.ctrlKey) && e.key === "Enter") {
        const tag = (e.target as HTMLElement)?.tagName;
        if (tag !== "TEXTAREA" && window.location.pathname !== "/generate") {
          e.preventDefault();
          router.push("/generate");
        }
      }
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [router, setCommandOpen]);

  useEffect(() => {
    const md = () => lastGenerate?.final_text || "";
    return registerExportShortcuts(md, md);
  }, [lastGenerate]);

  void commandOpen;
  return null;
}
