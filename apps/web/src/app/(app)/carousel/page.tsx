"use client";

import { useMemo, useState } from "react";
import { toast } from "sonner";
import { api } from "@/lib/api";
import { useWorkflowStore } from "@/lib/store";
import { Button } from "@/components/ui/button";
import { Card, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";

const THEMES = ["Minimal", "Academic", "Bold", "Soft"];
const LAYOUTS = ["single_column", "two_column", "comparison", "framework"];
const TYPEFACES = ["Geist", "Serif display", "Mono labels"];

export default function CarouselPage() {
  const lastGenerate = useWorkflowStore((s) => s.lastGenerate);
  const [topic, setTopic] = useState(lastGenerate?.topic || "");
  const [theme, setTheme] = useState("Minimal");
  const [layout, setLayout] = useState(LAYOUTS[0]);
  const [typeface, setTypeface] = useState(TYPEFACES[0]);
  const [busy, setBusy] = useState(false);
  const [result, setResult] = useState<Record<string, unknown> | null>(null);
  const [active, setActive] = useState(0);

  const slides = useMemo(() => {
    const graph = (result?.scene_graph || {}) as { slides?: Array<Record<string, unknown>> };
    return graph.slides || [];
  }, [result]);

  const svgs = (result?.svgs as string[] | undefined) || [];

  async function generate() {
    if (!topic.trim()) {
      toast.error("Topic is required");
      return;
    }
    setBusy(true);
    try {
      const data = await api.runCarousel({
        topic,
        draft: lastGenerate?.final_text,
        theme,
      });
      setResult(data);
      setActive(0);
      toast.success("Carousel generated");
    } catch (e) {
      toast.error(e instanceof Error ? e.message : "Carousel failed");
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-end justify-between gap-3">
        <div>
          <h1 className="text-2xl font-semibold tracking-tight">Carousel</h1>
          <p className="text-sm text-[var(--muted-foreground)]">
            Live preview via existing carousel pipeline adapter.
          </p>
        </div>
        <Button onClick={generate} disabled={busy}>
          {busy ? "Generating…" : "Generate carousel"}
        </Button>
      </div>

      <div className="grid gap-4 xl:grid-cols-[0.9fr_1.1fr]">
        <Card className="space-y-4">
          <label className="block space-y-1.5 text-sm">
            <span className="font-medium">Topic</span>
            <Input value={topic} onChange={(e) => setTopic(e.target.value)} />
          </label>
          <label className="block space-y-1.5 text-sm">
            <span className="font-medium">Theme</span>
            <select className="h-10 w-full rounded-xl border border-[var(--border)] bg-[var(--card)] px-3 text-sm" value={theme} onChange={(e) => setTheme(e.target.value)}>
              {THEMES.map((t) => (
                <option key={t}>{t}</option>
              ))}
            </select>
          </label>
          <label className="block space-y-1.5 text-sm">
            <span className="font-medium">Layout selector</span>
            <select className="h-10 w-full rounded-xl border border-[var(--border)] bg-[var(--card)] px-3 text-sm" value={layout} onChange={(e) => setLayout(e.target.value)}>
              {LAYOUTS.map((t) => (
                <option key={t}>{t}</option>
              ))}
            </select>
          </label>
          <label className="block space-y-1.5 text-sm">
            <span className="font-medium">Typography</span>
            <select className="h-10 w-full rounded-xl border border-[var(--border)] bg-[var(--card)] px-3 text-sm" value={typeface} onChange={(e) => setTypeface(e.target.value)}>
              {TYPEFACES.map((t) => (
                <option key={t}>{t}</option>
              ))}
            </select>
          </label>
          <CardDescription>
            Layout/typography selectors guide export intent. Theme is passed to the carousel pipeline.
          </CardDescription>
          <div className="space-y-2">
            <CardTitle className="text-sm">Slide list</CardTitle>
            {slides.length ? (
              slides.map((s, i) => (
                <button
                  key={i}
                  onClick={() => setActive(i)}
                  className={`flex w-full items-center justify-between rounded-xl border px-3 py-2 text-left text-sm ${
                    active === i ? "border-[var(--accent)] bg-[var(--accent-soft)]" : "border-[var(--border)]"
                  }`}
                >
                  <span>Slide {Number(s.slide_number || i + 1)}</span>
                  <Badge>{String(s.role || s.layout_id || "slide")}</Badge>
                </button>
              ))
            ) : (
              <CardDescription>No slides yet.</CardDescription>
            )}
          </div>
        </Card>

        <div className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>SVG preview</CardTitle>
              <CardDescription>
                {svgs[active] ? `slide ${active + 1}` : "Generate to preview"}
              </CardDescription>
            </CardHeader>
            <div className="flex min-h-[360px] items-center justify-center overflow-auto rounded-xl bg-[var(--muted)] p-4">
              {svgs[active] ? (
                <div className="w-full max-w-md" dangerouslySetInnerHTML={{ __html: svgs[active] }} />
              ) : (
                <span className="text-sm text-[var(--muted-foreground)]">No SVG yet</span>
              )}
            </div>
          </Card>
          <Card>
            <CardHeader>
              <CardTitle>Scene graph</CardTitle>
            </CardHeader>
            <pre className="max-h-64 overflow-auto rounded-xl bg-[var(--muted)] p-3 text-xs">
              {JSON.stringify(slides[active] || result?.scene_graph || {}, null, 2)}
            </pre>
          </Card>
          <div className="flex flex-wrap gap-2">
            <Button
              variant="outline"
              onClick={() => {
                const exports = (result?.exports || {}) as Record<string, unknown>;
                navigator.clipboard.writeText(JSON.stringify(exports, null, 2));
                toast.success("Export manifest copied");
              }}
            >
              Copy export manifest
            </Button>
            <Button variant="outline" onClick={() => navigator.clipboard.writeText(svgs[active] || "")}>
              Copy SVG
            </Button>
          </div>
        </div>
      </div>
    </div>
  );
}
