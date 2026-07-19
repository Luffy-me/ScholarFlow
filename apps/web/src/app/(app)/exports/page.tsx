"use client";

import { useState } from "react";
import { toast } from "sonner";
import { useWorkflowStore } from "@/lib/store";
import { Button } from "@/components/ui/button";
import { Card, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Textarea } from "@/components/ui/textarea";

function downloadText(filename: string, content: string, type = "text/plain") {
  const blob = new Blob([content], { type });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = filename;
  a.click();
  URL.revokeObjectURL(url);
}

export default function ExportsPage() {
  const lastGenerate = useWorkflowStore((s) => s.lastGenerate);
  const [text, setText] = useState(lastGenerate?.final_text || "");

  const linkedinVersion = text
    .replace(/\n{3,}/g, "\n\n")
    .trim();

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-semibold tracking-tight">Exports</h1>
        <p className="text-sm text-[var(--muted-foreground)]">
          Export markdown / copy LinkedIn version. Carousel binary exports come from carousel adapter manifests.
        </p>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Content</CardTitle>
          <CardDescription>Uses the latest generated draft from the backend pipeline.</CardDescription>
        </CardHeader>
        <Textarea rows={14} value={text} onChange={(e) => setText(e.target.value)} />
      </Card>

      <div className="flex flex-wrap gap-2">
        <Button
          onClick={() => {
            downloadText("scholarflow-post.md", text, "text/markdown");
            toast.success("Markdown downloaded");
          }}
        >
          Export Markdown
        </Button>
        <Button
          variant="outline"
          onClick={() => {
            navigator.clipboard.writeText(text);
            toast.success("Markdown copied");
          }}
        >
          Copy Markdown
        </Button>
        <Button
          variant="outline"
          onClick={() => {
            navigator.clipboard.writeText(linkedinVersion);
            toast.success("LinkedIn version copied");
          }}
        >
          Copy LinkedIn Version
        </Button>
        <Button
          variant="outline"
          onClick={() => {
            downloadText(
              "scholarflow-post.txt",
              linkedinVersion,
              "text/plain",
            );
            toast.message("Plain text exported (PDF/PPTX/PNG via carousel exports)");
          }}
        >
          Export TXT
        </Button>
        <Button
          variant="secondary"
          onClick={() => {
            toast.message("Open Carousel to generate SVG/PNG/PDF/PPTX via export engine");
          }}
        >
          PDF / PPTX / PNG / SVG
        </Button>
      </div>
    </div>
  );
}
