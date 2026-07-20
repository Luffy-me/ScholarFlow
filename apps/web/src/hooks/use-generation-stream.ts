"use client";

import { useCallback } from "react";
import { toast } from "sonner";
import { api } from "@/lib/api";
import {
  buildVersionTimeline,
  runGenerationWithReplay,
  splitParagraphs,
} from "@/lib/generation-stream";
import { useWorkflowStore, defaultStages } from "@/lib/store";
import type { GenerateRequest, PipelineStageId } from "@/types/api";

const STAGE_ORDER: PipelineStageId[] = [
  "research",
  "reasoning",
  "writing",
  "claim_check",
  "humanizer",
  "optimizer",
  "editorial",
  "carousel",
  "export",
];

function mapRunningToStages(runningId: PipelineStageId) {
  const idx = STAGE_ORDER.indexOf(runningId);
  return defaultStages.map((s) => {
    const si = STAGE_ORDER.indexOf(s.id);
    if (si < idx) return { ...s, status: "completed" as const };
    if (s.id === runningId) return { ...s, status: "running" as const };
    if (
      runningId === "writing" &&
      (s.id === "claim_check" || s.id === "humanizer")
    ) {
      return { ...s, status: "running" as const };
    }
    if (runningId === "optimizer" && s.id === "claim_check") {
      return { ...s, status: "completed" as const };
    }
    return { ...s, status: "pending" as const };
  });
}

export function useGenerationStream() {
  const run = useCallback(async (request: GenerateRequest, options?: { retryFromStage?: PipelineStageId }) => {
    const retryFrom = options?.retryFromStage;
    const state = useWorkflowStore.getState();
    const cached = retryFrom ? state.cachedGenerateResult : null;

    state.resetStream();
    useWorkflowStore.getState().setStreamMeta({
      isStreaming: true,
      streamPhase: cached ? "replaying" : "waiting-api",
      lastRequest: request,
      failedStage: null,
      streamError: null,
      cachedGenerateResult: cached ?? state.cachedGenerateResult,
    });
    useWorkflowStore.getState().setStages(defaultStages.map((s) => ({ ...s, status: "pending" })));

    const started = Date.now();

    try {
      const { result, carouselSvgs, carouselResult } = await runGenerationWithReplay({
        request,
        generate: api.generate,
        runCarousel: (p) => api.runCarousel({ ...p, theme: "Minimal" }),
        fromStage: retryFrom,
        cachedResult: cached ?? undefined,
        onStageRunning: (stage) => {
          useWorkflowStore.getState().setStreamMeta({ streamPhase: "replaying" });
          useWorkflowStore.getState().setStages(mapRunningToStages(stage));
        },
        onMilestone: (label) => {
          const s = useWorkflowStore.getState();
          s.pushTimelineEvent(label);
          const stageMap: Record<string, PipelineStageId> = {
            "Research Complete": "research",
            "Reasoning Complete": "reasoning",
            "Writing Complete": "writing",
            "Optimization Complete": "optimizer",
            "Editorial Review Complete": "editorial",
            "Carousel Complete": "carousel",
            Final: "export",
          };
          const id = stageMap[label];
          if (id) {
            s.markStage(id, "completed", undefined, Date.now() - started);
          }
        },
        onResearchSource: (src) => useWorkflowStore.getState().appendResearchSource(src),
        onResearchEvidence: (ev) => useWorkflowStore.getState().appendResearchEvidence(ev),
        onResearchSummary: (summary) => useWorkflowStore.getState().setResearchSummary(summary),
        onReasoningReady: (sections) => useWorkflowStore.getState().setReasoningSections(sections),
        onParagraph: (_i, _t, paragraph) => useWorkflowStore.getState().appendStreamedParagraph(paragraph),
        onCarouselSvg: (index) => useWorkflowStore.getState().setCarouselVisibleCount(index + 1),
        onComplete: (genResult) => {
          const s = useWorkflowStore.getState();
          s.setLastGenerate(genResult);
          s.setStreamMeta({
            isStreaming: false,
            streamPhase: "done",
            cachedGenerateResult: genResult,
          });
          s.setVersionTimeline(buildVersionTimeline(genResult));
          s.pushVersion(genResult.final_text || genResult.draft, "Generated");
          const paragraphs = splitParagraphs(genResult.final_text || genResult.draft);
          if (!s.streamedParagraphs.length && paragraphs.length) {
            s.setStreamedParagraphs(paragraphs);
          }
          s.markStage("export", "completed", "Ready", Date.now() - started);
          toast.success("Generation complete");
        },
        onError: (stage, error) => {
          useWorkflowStore.getState().setStreamMeta({
            isStreaming: false,
            streamPhase: "error",
            failedStage: stage,
            streamError: error.message,
          });
          useWorkflowStore.getState().markStage(stage, "error", error.message);
        },
      });

      if (carouselResult) {
        useWorkflowStore.getState().setCarouselState(carouselResult, carouselSvgs, carouselSvgs.length);
      } else if (carouselSvgs.length) {
        useWorkflowStore.getState().setCarouselState(null, carouselSvgs, carouselSvgs.length);
      }
      useWorkflowStore.getState().setStreamMeta({ cachedGenerateResult: result });

      return result;
    } catch (error) {
      const message = error instanceof Error ? error.message : "Generation failed";
      const s = useWorkflowStore.getState();
      s.setStreamMeta({
        isStreaming: false,
        streamPhase: "error",
        streamError: message,
        failedStage: s.failedStage ?? "research",
      });
      toast.error(message);
      throw error;
    }
  }, []);

  const retryFailedStep = useCallback(async () => {
    const { lastRequest, failedStage, cachedGenerateResult } = useWorkflowStore.getState();
    if (!lastRequest) {
      toast.error("No generation to retry");
      return;
    }
    if (cachedGenerateResult && failedStage && failedStage !== "research") {
      await run(lastRequest, { retryFromStage: failedStage });
      return;
    }
    await run(lastRequest);
  }, [run]);

  return { run, retryFailedStep };
}
