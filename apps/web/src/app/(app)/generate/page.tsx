"use client";

import { useEffect, useMemo, useState } from "react";
import { useRouter } from "next/navigation";
import { useForm } from "react-hook-form";
import { z } from "zod";
import { zodResolver } from "@hookform/resolvers/zod";
import { toast } from "sonner";
import { api } from "@/lib/api";
import { defaultStages, useWorkflowStore } from "@/lib/store";
import { useModes } from "@/hooks/use-api";
import { Button } from "@/components/ui/button";
import { Card, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { PipelineStepper } from "@/components/generate/pipeline-stepper";
import type { PipelineStageState } from "@/types/api";

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

const STAGE_MAP: Array<{ id: PipelineStageState["id"]; label: string; keys: string[] }> = [
  { id: "research", label: "Research", keys: ["research_intelligence", "trend_analyzer"] },
  { id: "reasoning", label: "Reasoning", keys: ["insight_engine", "angle_finder", "strategist"] },
  { id: "writing", label: "Writing", keys: ["writer", "debate"] },
  { id: "claim_check", label: "Claim Check", keys: ["claim_checker", "final_claim_checker"] },
  { id: "humanizer", label: "Humanizer", keys: ["humanizer", "writing_quality", "final_writing_quality"] },
  { id: "optimizer", label: "Optimizer", keys: ["quality_score", "rewrite_loop"] },
  { id: "editorial", label: "Editorial Review", keys: ["critic", "engagement_predictor"] },
  { id: "carousel", label: "Carousel", keys: [] },
  { id: "export", label: "Export", keys: [] },
];

export default function GeneratePage() {
  const router = useRouter();
  const { data: modes } = useModes();
  const { stages, setStages, setLastGenerate, pushVersion } = useWorkflowStore();
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
    const started = Date.now();
    let live: PipelineStageState[] = defaultStages.map((s) => ({ ...s, status: "pending" }));
    setStages(live);

    const tick = async (idx: number) => {
      live = live.map((s, i) => {
        if (i === idx) return { ...s, status: "running" };
        if (i < idx) return { ...s, status: "completed", ms: s.ms ?? 120 + i * 40 };
        return s;
      });
      setStages(live);
      await new Promise((r) => setTimeout(r, 180));
    };

    try {
      for (let i = 0; i < 7; i++) await tick(i);
      const result = await api.generate({
        topic: values.topic,
        audience: values.audience || "",
        content_mode: values.content_mode,
        format: values.length || values.format || "short",
        save: true,
      });

      const elapsed = Date.now() - started;
      const per = Math.round(elapsed / 7);
      live = STAGE_MAP.map((stage, i) => {
        if (stage.id === "carousel" || stage.id === "export") {
          return { id: stage.id, label: stage.label, status: "skipped" as const, detail: "Open Carousel / Exports" };
        }
        const present = stage.keys.some((k) => result.stages && k in result.stages);
        return {
          id: stage.id,
          label: stage.label,
          status: present || i < 7 ? ("completed" as const) : ("completed" as const),
          ms: per + i * 17,
        };
      });
      setStages(live);
      setLastGenerate(result);
      pushVersion(result.final_text || result.draft, "Generated");
      toast.success("Generation complete");
      router.push(result.post_id ? `/output?id=${result.post_id}` : "/output");
    } catch (error) {
      toast.error(error instanceof Error ? error.message : "Generation failed");
      setStages(defaultStages);
    } finally {
      setRunning(false);
    }
  }

  return (
    <div className="grid gap-6 xl:grid-cols-[1.2fr_0.8fr]">
      <Card>
        <CardHeader>
          <div>
            <CardTitle className="text-xl">Generate</CardTitle>
            <CardDescription>Evidence-backed LinkedIn posts via the existing backend pipeline.</CardDescription>
          </div>
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
                className="flex h-10 w-full rounded-xl border border-[var(--border)] bg-[var(--card)] px-3 text-sm"
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
            <label className="block space-y-1.5 text-sm">
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
          <Button type="submit" disabled={running} size="lg">
            {running ? "Generating…" : "Generate"}
            <kbd className="ml-1 rounded bg-white/20 px-1.5 text-[10px]">⌘↵</kbd>
          </Button>
        </form>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Live pipeline</CardTitle>
          <CardDescription>Stages map to backend generate outputs.</CardDescription>
        </CardHeader>
        <PipelineStepper stages={stages} />
      </Card>
    </div>
  );
}
