"use client";

import { useEffect, useMemo, useState } from "react";
import Link from "next/link";
import { useForm } from "react-hook-form";
import { z } from "zod";
import { zodResolver } from "@hookform/resolvers/zod";
import { useModes } from "@/hooks/use-api";
import { useGenerationStream } from "@/hooks/use-generation-stream";
import { useWorkflowStore } from "@/lib/store";
import { Button } from "@/components/ui/button";
import { Card, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { PipelineStepper } from "@/components/generate/pipeline-stepper";
import { ThinkingTimeline } from "@/components/generate/thinking-timeline";
import { LiveResearchPanel } from "@/components/generate/live-research-panel";
import { LiveReasoningPanel } from "@/components/generate/live-reasoning-panel";
import { StreamingPost } from "@/components/generate/streaming-post";
import { VersionTimeline } from "@/components/generate/version-timeline";
import { ErrorRetry } from "@/components/ui/error-retry";
import { ExportActions } from "@/components/export/export-actions";
import { Skeleton } from "@/components/ui/skeleton";

const schema = z.object({
  topic: z.string().min(3, "Topic is required"),
  audience: z.string(),
  goal: z.string(),
  content_mode: z.string(),
  format: z.string(),
  tone: z.string(),
  length: z.string(),
});

type FormValues = z.infer<typeof schema>;

export default function GeneratePage() {
  const { data: modes } = useModes();
  const { run, retryFailedStep } = useGenerationStream();
  const {
    stages,
    isStreaming,
    streamPhase,
    timelineEvents,
    visibleResearch,
    reasoningSections,
    streamedParagraphs,
    streamError,
    failedStage,
    versionTimeline,
    lastGenerate,
    carouselSvgs,
    carouselResult,
  } = useWorkflowStore();

  const [running, setRunning] = useState(false);

  const form = useForm<FormValues>({
    resolver: zodResolver(schema),
    defaultValues: {
      topic: "",
      audience: "builders",
      goal: "Share an evidence-backed insight",
      content_mode: "founder",
      format: "short",
      tone: "clear",
      length: "short",
    },
  });

  useEffect(() => {
    if (modes?.default_mode) form.setValue("content_mode", modes.default_mode);
  }, [modes, form]);

  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      if ((e.metaKey || e.ctrlKey) && e.key === "Enter" && !running) {
        e.preventDefault();
        form.handleSubmit(onSubmit)();
      }
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  });

  const modeOptions = useMemo(() => Object.keys(modes?.modes || { founder: {} }), [modes]);

  async function onSubmit(values: FormValues) {
    setRunning(true);
    try {
      await run({
        topic: values.topic,
        audience: values.audience || "",
        content_mode: values.content_mode,
        format: values.length || values.format || "short",
        save: true,
      });
    } catch {
      /* toast in hook */
    } finally {
      setRunning(false);
    }
  }

  const showWorkspace = isStreaming || streamPhase === "done" || streamPhase === "error";
  const exportsManifest = (carouselResult?.exports || {}) as Record<string, unknown>;

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-end justify-between gap-3">
        <div>
          <h1 className="text-2xl font-semibold tracking-tight">Generate</h1>
          <p className="text-sm text-[var(--muted-foreground)]">
            Live progress through research, reasoning, writing, and review — without leaving this view.
          </p>
        </div>
        {streamPhase === "done" && lastGenerate?.post_id ? (
          <Button asChild variant="outline">
            <Link href={`/output?id=${lastGenerate.post_id}`}>Open in editor</Link>
          </Button>
        ) : null}
      </div>

      {streamError ? (
        <ErrorRetry
          message={streamError}
          stage={failedStage}
          busy={running}
          onRetry={() => {
            setRunning(true);
            void retryFailedStep().finally(() => setRunning(false));
          }}
        />
      ) : null}

      <div className="grid gap-6 xl:grid-cols-[minmax(0,1fr)_minmax(0,1.15fr)]">
        <Card>
          <CardHeader>
            <CardTitle className="text-xl">Brief</CardTitle>
            <CardDescription>⌘↵ to generate · streaming workspace on the right</CardDescription>
          </CardHeader>
          <form className="space-y-4" onSubmit={form.handleSubmit(onSubmit)}>
            <label className="block space-y-1.5 text-sm">
              <span className="font-medium">Topic</span>
              <Textarea rows={3} placeholder="What constraint or insight should we explore?" {...form.register("topic")} />
              {form.formState.errors.topic ? (
                <span className="text-xs text-[var(--danger)]">{form.formState.errors.topic.message}</span>
              ) : null}
            </label>
            <div className="grid gap-4 md:grid-cols-2">
              <label className="block space-y-1.5 text-sm">
                <span className="font-medium">Audience</span>
                <Input {...form.register("audience")} />
              </label>
              <label className="block space-y-1.5 text-sm">
                <span className="font-medium">Goal</span>
                <Input {...form.register("goal")} />
              </label>
              <label className="block space-y-1.5 text-sm">
                <span className="font-medium">Content type / mode</span>
                <select
                  className="flex h-10 w-full rounded-xl border border-[var(--border)] bg-[var(--card)] px-3 text-sm transition-colors focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[var(--accent)]"
                  {...form.register("content_mode")}
                >
                  {modeOptions.map((m) => (
                    <option key={m} value={m}>
                      {modes?.modes?.[m]?.label || m}
                    </option>
                  ))}
                </select>
              </label>
              <label className="block space-y-1.5 text-sm">
                <span className="font-medium">Tone</span>
                <Input {...form.register("tone")} placeholder="clear, rigorous, practical" />
              </label>
              <label className="block space-y-1.5 text-sm md:col-span-2">
                <span className="font-medium">Length</span>
                <select
                  className="flex h-10 w-full rounded-xl border border-[var(--border)] bg-[var(--card)] px-3 text-sm"
                  {...form.register("length")}
                >
                  <option value="short">Short</option>
                  <option value="medium">Medium</option>
                  <option value="long">Long</option>
                </select>
              </label>
            </div>
            <Button type="submit" disabled={running || isStreaming} size="lg" className="transition-transform active:scale-[0.98]">
              {running || isStreaming ? "Generating…" : "Generate"}
              <kbd className="ml-1 rounded bg-white/20 px-1.5 text-[10px]">⌘↵</kbd>
            </Button>
          </form>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Pipeline</CardTitle>
            <CardDescription>
              {streamPhase === "waiting-api" ? "Waiting for backend…" : "Research → Reasoning → Writing → Optimization → Editorial → Carousel → Final"}
            </CardDescription>
          </CardHeader>
          {streamPhase === "waiting-api" && !showWorkspace ? (
            <div className="space-y-2 px-4 pb-4">
              <Skeleton className="h-10" />
              <Skeleton className="h-10" />
              <Skeleton className="h-10" />
            </div>
          ) : (
            <div className="px-4 pb-4">
              <PipelineStepper stages={stages} />
            </div>
          )}
          <div className="border-t border-[var(--border)] px-4 py-4">
            <CardTitle className="mb-3 text-sm">Thinking timeline</CardTitle>
            <ThinkingTimeline events={timelineEvents} />
          </div>
        </Card>
      </div>

      {showWorkspace ? (
        <div className="grid gap-6 xl:grid-cols-2">
          <Card>
            <CardHeader>
              <CardTitle>Live research</CardTitle>
            </CardHeader>
            <LiveResearchPanel
              sources={visibleResearch.sources}
              evidence={visibleResearch.evidence}
              summary={visibleResearch.summary}
              loading={streamPhase === "waiting-api"}
            />
          </Card>
          <Card>
            <CardHeader>
              <CardTitle>Live reasoning</CardTitle>
            </CardHeader>
            <LiveReasoningPanel sections={reasoningSections} />
          </Card>
          <Card className="xl:col-span-2">
            <CardHeader>
              <CardTitle>Streaming post</CardTitle>
              <CardDescription>Paragraphs reveal as writing completes.</CardDescription>
            </CardHeader>
            <div className="px-4 pb-4">
              <StreamingPost
                paragraphs={streamedParagraphs}
                streaming={isStreaming && streamPhase === "replaying"}
              />
            </div>
            {streamPhase === "done" ? (
              <div className="border-t border-[var(--border)] px-4 py-4 space-y-3">
                <ExportActions
                  markdown={lastGenerate?.final_text || streamedParagraphs.join("\n\n")}
                  carouselExports={exportsManifest}
                  carouselSvgs={carouselSvgs}
                />
              </div>
            ) : null}
          </Card>
          {versionTimeline.length ? (
            <Card className="xl:col-span-2">
              <CardHeader>
                <CardTitle>Version timeline</CardTitle>
              </CardHeader>
              <div className="px-4 pb-4">
                <VersionTimeline versions={versionTimeline} />
              </div>
            </Card>
          ) : null}
        </div>
      ) : null}
    </div>
  );
}
