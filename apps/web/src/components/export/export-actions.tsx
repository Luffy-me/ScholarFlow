"use client";

import { toast } from "sonner";
import { Button } from "@/components/ui/button";

function downloadText(filename: string, content: string, type = "text/plain") {
  const blob = new Blob([content], { type });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = filename;
  a.click();
  URL.revokeObjectURL(url);
}

function downloadSvgPng(svg: string, filename: string) {
  const blob = new Blob([svg], { type: "image/svg+xml" });
  const url = URL.createObjectURL(blob);
  const img = new Image();
  img.onload = () => {
    const canvas = document.createElement("canvas");
    canvas.width = img.width || 1080;
    canvas.height = img.height || 1080;
    const ctx = canvas.getContext("2d");
    if (ctx) {
      ctx.fillStyle = "#ffffff";
      ctx.fillRect(0, 0, canvas.width, canvas.height);
      ctx.drawImage(img, 0, 0);
      canvas.toBlob((b) => {
        if (!b) return;
        const pngUrl = URL.createObjectURL(b);
        const a = document.createElement("a");
        a.href = pngUrl;
        a.download = filename;
        a.click();
        URL.revokeObjectURL(pngUrl);
      });
    }
    URL.revokeObjectURL(url);
  };
  img.src = url;
}

export function ExportActions({
  markdown,
  linkedin,
  carouselExports,
  carouselSvgs,
}: {
  markdown: string;
  linkedin?: string;
  carouselExports?: Record<string, unknown>;
  carouselSvgs?: string[];
}) {
  const linkedInText = linkedin ?? markdown.replace(/\n{3,}/g, "\n\n").trim();

  return (
    <div className="flex flex-wrap gap-2">
      <Button
        size="sm"
        onClick={() => {
          void navigator.clipboard.writeText(markdown);
          toast.success("Markdown copied");
        }}
      >
        Copy Markdown
      </Button>
      <Button
        size="sm"
        variant="outline"
        onClick={() => {
          void navigator.clipboard.writeText(linkedInText);
          toast.success("LinkedIn copy ready");
        }}
      >
        Copy LinkedIn
        <kbd className="ml-1 rounded bg-[var(--muted)] px-1 text-[10px]">⌘⇧C</kbd>
      </Button>
      <Button
        size="sm"
        variant="outline"
        onClick={() => {
          downloadText("scholarflow-post.md", markdown, "text/markdown");
          toast.success("Markdown downloaded");
        }}
      >
        Download MD
      </Button>
      <Button
        size="sm"
        variant="outline"
        onClick={() => {
          const paths = carouselExports || {};
          const pptx = Object.values(paths).find((v) => String(v).endsWith(".pptx"));
          if (pptx && typeof pptx === "string") {
            toast.message(`PPTX path: ${pptx} (open from carousel export manifest)`);
          } else {
            toast.message("Generate carousel for PPTX export paths");
          }
        }}
      >
        Download PPTX
      </Button>
      <Button
        size="sm"
        variant="outline"
        onClick={() => {
          const paths = carouselExports || {};
          const pdf = Object.values(paths).find((v) => String(v).endsWith(".pdf"));
          if (pdf) toast.message(`PDF: ${String(pdf)}`);
          else toast.message("Generate carousel for PDF paths");
        }}
      >
        Download PDF
      </Button>
      <Button
        size="sm"
        variant="outline"
        onClick={() => {
          const svg = carouselSvgs?.[0];
          if (svg) downloadSvgPng(svg, "scholarflow-slide-1.png");
          else toast.message("Generate carousel for PNG export");
        }}
      >
        Download PNG
      </Button>
    </div>
  );
}

export function registerExportShortcuts(getMarkdown: () => string, getLinkedIn?: () => string) {
  const onKey = (e: KeyboardEvent) => {
    if (!(e.metaKey || e.ctrlKey)) return;
    if (e.key.toLowerCase() === "s") {
      e.preventDefault();
      downloadText("scholarflow-post.md", getMarkdown(), "text/markdown");
      toast.success("Exported markdown");
    }
    if (e.shiftKey && e.key.toLowerCase() === "c") {
      e.preventDefault();
      const text = getLinkedIn?.() ?? getMarkdown();
      void navigator.clipboard.writeText(text.replace(/\n{3,}/g, "\n\n").trim());
      toast.success("LinkedIn copied");
    }
  };
  window.addEventListener("keydown", onKey);
  return () => window.removeEventListener("keydown", onKey);
}
