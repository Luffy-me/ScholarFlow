"use client";

import { useEffect, useMemo, useState } from "react";
import { toast } from "sonner";
import { motion } from "framer-motion";
import { api } from "@/lib/api";
import { useWorkflowStore } from "@/lib/store";
import { Button } from "@/components/ui/button";
import { Card, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { EmptyState } from "@/components/ui/empty-state";
import { Layers3 } from "lucide-react";

const THEMES = ["Minimal", "Academic", "Bold", "Soft"];
const LAYOUTS = ["single_column", "two_column", "comparison", "framework"];
const TYPEFACES = ["Geist", "Serif display", "Mono labels"];

export default function CarouselPage() {
  const lastGenerate = useWorkflowStore((s) => s.lastGenerate);
  const storedSvgs = useWorkflowStore((s) => s.carouselSvgs);
  const [topic, setTopic] = useState(lastGenerate?.topic || "");
  const [theme, setTheme] = useState("Minimal");
  const [layout, setLayout] = useState(LAYOUTS[0]);
  const [typeface, setTypeface] = useState(TYPEFACES[0]);
  const [busy, setBusy] = useState(false);
  const [result, setResult] = useState<Record<string, unknown> | null>(null);
  const [active, setActive] = useState(0);
  const [visibleCount, setVisibleCount] = useState(0);

  const slides = useMemo(() => {
    const graph = (result?.scene_graph || {}) as { slides?: Array<Record<string, unknown>> };
    return graph.slides || [];
  }, [result]);

  const svgs = (result?.svgs as string[] | undefined) || storedSvgs || [];
  const visibleSvgs = svgs.slice(0, visibleCount);

  useEffect(() => {
    if (!busy && svgs.length && visibleCount < svgs.length) {
      const t = window.setInterval(() => {
        setVisibleCount((c) => {
          if (c >= svgs.length) {
            window.clearInterval(t);
            return c;
          }
          return c + 1;
        });
      }, 140);
      return () => window.clearInterval(t);
    }
  }, [busy, svgs.length, visibleCount]);

  async function generate() {
    if (!topic.trim()) {
      toast.error("Topic is required");
      return;
    }
    setBusy(true);
    setVisibleCount(0);
    setResult(null);
    try {
      const data = await api.runCarousel({
        topic,
        draft: lastGenerate?.final_text,
        theme,
      });
      setResult(data);
      useWorkflowStore.getState().setCarouselState(data, (data.svgs as string[]) || [], 0);
      setActive(0);
      const count = ((data.svgs as string[]) || []).length;
      for (let i = 0; i < count; i++) {
        await new Promise((r) => setTimeout(r, 160));
        setVisibleCount(i + 1);
        useWorkflowStore.getState().setCarouselVisibleCount(i + 1);
      }
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
            Slides render as each SVG completes — no waiting for the full deck.
          </p>
        </div>
        <Button onClick={generate} disabled={busy} className="transition-transform active:scale-[0.98]">
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
            <select
              className="h-10 w-full rounded-xl border border-[var(--border)] bg-[var(--card)] px-3 text-sm"
              value={theme}
              onChange={(e) => setTheme(e.target.value)}
            >
              {THEMES.map((t) => (
                <option key={t}>{t}</option>
              ))}
            </select>
          </label>
          <label className="block space-y-1.5 text-sm">
            <span className="font-medium">Layout selector</span>
            <select
              className="h-10 w-full rounded-xl border border-[var(--border)] bg-[var(--card)] px-3 text-sm"
              value={layout}
              onChange={(e) => setLayout(e.target.value)}
            >
              {LAYOUTS.map((t) => (
                <option key={t}>{t}</option>
              ))}
            </select>
          </label>
          <label className="block space-y-1.5 text-sm">
            <span className="font-medium">Typography</span>
            <select
              className="h-10 w-full rounded-xl border border-[var(--border)] bg-[var(--card)] px-3 text-sm"
              value={typeface}
              onChange={(e) => setTypeface(e.target.value)}
            >
              {TYPEFACES.map((t) => (
                <option key={t}>{t}</option>
              ))}
            </select>
          </label>
          <div className="space-y-2">
            <CardTitle className="text-sm">Slide list</CardTitle>
            {slides.length ? (
              slides.map((s, i) => (
                <button
                  key={i}
                  type="button"
                  onClick={() => setActive(i)}
                  disabled={i >= visibleCount}
                  className={`flex w-full items-center justify-between rounded-xl border px-3 py-2 text-left text-sm transition-colors hover:bg-[var(--muted)] ${
                    active === i ? "border-[var(--accent)] bg-[var(--accent-soft)]" : "border-[var(--border)]"
                  } ${i >= visibleCount ? "opacity-40" : ""}`}
                >
                  <span>Slide {Number(s.slide_number || i + 1)}</span>
                  <Badge>{String(s.role || s.layout_id || "slide")}</Badge>
                </button>
              ))
            ) : busy ? (
              <div className="space-y-2">
                <Skeleton className="h-10" />
                <Skeleton className="h-10" />
              </div>
            ) : (
              <EmptyState icon={Layers3} title="No slides yet." description="Generate a carousel to preview slides live." />
            )}
          </div>
        </Card>

        <div className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Live preview</CardTitle>
              <CardDescription>
                {visibleSvgs[active] ? `Slide ${active + 1} of ${svgs.length}` : busy ? "Rendering slides…" : "Generate to preview"}
              </CardDescription>
            </CardHeader>
            <div className="grid gap-3 p-4 sm:grid-cols-2">
              {visibleSvgs.length ? (
                visibleSvgs.map((svg, i) => (
                  <motion.button
                    type="button"
                    key={i}
                    initial={{ opacity: 0, scale: 0.98 }}
                    animate={{ opacity: 1, scale: 1 }}
                    onClick={() => setActive(i)}
                    className={`overflow-hidden rounded-xl border bg-[var(--muted)] p-2 transition-shadow hover:shadow-md ${
                      active === i ? "border-[var(--accent)]" : "border-[var(--border)]"
                    }`}
                  >
                    <div className="pointer-events-none" dangerouslySetInnerHTML={{ __html: svg }} />
                  </motion.button>
                ))
              ) : (
                <div className="col-span-2 flex min-h-[360px] items-center justify-center rounded-xl bg-[var(--muted)]">
                  {busy ? <Skeleton className="h-64 w-full max-w-md" /> : (
                    <span className="text-sm text-[var(--muted-foreground)]">No SVG yet</span>
                  )}
                </div>
              )}
            </div>
          </Card>
        </div>
      </div>
    </div>
  );
}
