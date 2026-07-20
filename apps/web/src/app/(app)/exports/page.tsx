"use client";

import { useEffect, useState } from "react";
import { useWorkflowStore } from "@/lib/store";
import { ExportActions } from "@/components/export/export-actions";
import { Card, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Textarea } from "@/components/ui/textarea";

export default function ExportsPage() {
  const lastGenerate = useWorkflowStore((s) => s.lastGenerate);
  const carouselResult = useWorkflowStore((s) => s.carouselResult);
  const carouselSvgs = useWorkflowStore((s) => s.carouselSvgs);
  const [text, setText] = useState(lastGenerate?.final_text || "");

  useEffect(() => {
    if (lastGenerate?.final_text) setText(lastGenerate.final_text);
  }, [lastGenerate]);

  const exportsManifest = (carouselResult?.exports || {}) as Record<string, unknown>;

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-semibold tracking-tight">Exports</h1>
        <p className="text-sm text-[var(--muted-foreground)]">
          One-click copy and download. ⌘S exports markdown · ⌘⇧C copies LinkedIn.
        </p>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Content</CardTitle>
          <CardDescription>Latest generated draft from the pipeline.</CardDescription>
        </CardHeader>
        <Textarea rows={14} value={text} onChange={(e) => setText(e.target.value)} className="font-mono text-sm" />
        <div className="border-t border-[var(--border)] p-4">
          <ExportActions markdown={text} carouselExports={exportsManifest} carouselSvgs={carouselSvgs} />
        </div>
      </Card>
    </div>
  );
}
