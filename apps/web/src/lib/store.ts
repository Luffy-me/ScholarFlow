"use client";

import { create } from "zustand";
import { persist } from "zustand/middleware";
import type {
  GenerateRequest,
  GenerateResponse,
  PipelineStageId,
  PipelineStageState,
  ResearchEvidence,
  ResearchSource,
} from "@/types/api";
import type { extractReasoningSections } from "@/lib/generation-stream";

export type TimelineEvent = {
  id: string;
  label: string;
  at: string;
};

export type ReasoningSections = ReturnType<typeof extractReasoningSections>;

type WorkflowState = {
  lastGenerate: GenerateResponse | null;
  stages: PipelineStageState[];
  draftVersions: Array<{ id: string; text: string; at: string; label: string }>;
  versionTimeline: Array<{ id: string; label: string; text: string; at: string }>;
  theme: "light" | "dark" | "system";
  inspectorOpen: boolean;
  isStreaming: boolean;
  streamPhase: "idle" | "waiting-api" | "replaying" | "done" | "error";
  timelineEvents: TimelineEvent[];
  visibleResearch: {
    sources: ResearchSource[];
    evidence: ResearchEvidence[];
    summary: string;
  };
  reasoningSections: ReasoningSections | null;
  streamedParagraphs: string[];
  carouselSvgs: string[];
  carouselSvgsVisible: number;
  carouselResult: Record<string, unknown> | null;
  failedStage: PipelineStageId | null;
  streamError: string | null;
  lastRequest: GenerateRequest | null;
  cachedGenerateResult: GenerateResponse | null;
  setTheme: (theme: "light" | "dark" | "system") => void;
  setInspectorOpen: (open: boolean) => void;
  setLastGenerate: (value: GenerateResponse | null) => void;
  setStages: (stages: PipelineStageState[]) => void;
  pushVersion: (text: string, label: string) => void;
  restoreVersion: (id: string) => string | null;
  resetStream: () => void;
  setStreamMeta: (patch: Partial<Pick<WorkflowState, "isStreaming" | "streamPhase" | "failedStage" | "streamError" | "lastRequest" | "cachedGenerateResult">>) => void;
  pushTimelineEvent: (label: string) => void;
  appendResearchSource: (source: ResearchSource) => void;
  appendResearchEvidence: (evidence: ResearchEvidence) => void;
  setResearchSummary: (summary: string) => void;
  setReasoningSections: (sections: ReasoningSections) => void;
  setStreamedParagraphs: (paragraphs: string[]) => void;
  appendStreamedParagraph: (paragraph: string) => void;
  setCarouselState: (result: Record<string, unknown> | null, svgs: string[], visible: number) => void;
  setCarouselVisibleCount: (count: number) => void;
  setVersionTimeline: (versions: WorkflowState["versionTimeline"]) => void;
  markStage: (id: PipelineStageId, status: PipelineStageState["status"], detail?: string, ms?: number) => void;
};

const defaultStages: PipelineStageState[] = [
  { id: "research", label: "Research", status: "pending" },
  { id: "reasoning", label: "Reasoning", status: "pending" },
  { id: "writing", label: "Writing", status: "pending" },
  { id: "claim_check", label: "Claim Check", status: "pending" },
  { id: "humanizer", label: "Humanizer", status: "pending" },
  { id: "optimizer", label: "Optimizer", status: "pending" },
  { id: "editorial", label: "Editorial Review", status: "pending" },
  { id: "carousel", label: "Carousel", status: "pending" },
  { id: "export", label: "Final", status: "pending" },
];

const emptyResearch = () => ({
  sources: [] as ResearchSource[],
  evidence: [] as ResearchEvidence[],
  summary: "",
});

export const useWorkflowStore = create<WorkflowState>()(
  persist(
    (set, get) => ({
      lastGenerate: null,
      stages: defaultStages,
      draftVersions: [],
      versionTimeline: [],
      theme: "system",
      inspectorOpen: true,
      isStreaming: false,
      streamPhase: "idle",
      timelineEvents: [],
      visibleResearch: emptyResearch(),
      reasoningSections: null,
      streamedParagraphs: [],
      carouselSvgs: [],
      carouselSvgsVisible: 0,
      carouselResult: null,
      failedStage: null,
      streamError: null,
      lastRequest: null,
      cachedGenerateResult: null,
      setTheme: (theme) => set({ theme }),
      setInspectorOpen: (inspectorOpen) => set({ inspectorOpen }),
      setLastGenerate: (lastGenerate) => set({ lastGenerate }),
      setStages: (stages) => set({ stages }),
      pushVersion: (text, label) =>
        set({
          draftVersions: [
            {
              id: `${Date.now()}`,
              text,
              at: new Date().toISOString(),
              label,
            },
            ...get().draftVersions,
          ].slice(0, 30),
        }),
      restoreVersion: (id) => {
        const hit = get().draftVersions.find((v) => v.id === id);
        return hit?.text ?? null;
      },
      resetStream: () =>
        set({
          streamPhase: "idle",
          isStreaming: false,
          timelineEvents: [],
          visibleResearch: emptyResearch(),
          reasoningSections: null,
          streamedParagraphs: [],
          carouselSvgs: [],
          carouselSvgsVisible: 0,
          carouselResult: null,
          failedStage: null,
          streamError: null,
          stages: defaultStages.map((s) => ({ ...s, status: "pending" })),
        }),
      setStreamMeta: (patch) => set(patch),
      pushTimelineEvent: (label) =>
        set({
          timelineEvents: [
            ...get().timelineEvents,
            { id: `${Date.now()}-${label}`, label, at: new Date().toISOString() },
          ],
        }),
      appendResearchSource: (source) =>
        set({
          visibleResearch: {
            ...get().visibleResearch,
            sources: [...get().visibleResearch.sources, source],
          },
        }),
      appendResearchEvidence: (evidence) =>
        set({
          visibleResearch: {
            ...get().visibleResearch,
            evidence: [...get().visibleResearch.evidence, evidence],
          },
        }),
      setResearchSummary: (summary) =>
        set({
          visibleResearch: { ...get().visibleResearch, summary },
        }),
      setReasoningSections: (reasoningSections) => set({ reasoningSections }),
      setStreamedParagraphs: (streamedParagraphs) => set({ streamedParagraphs }),
      appendStreamedParagraph: (paragraph) =>
        set({ streamedParagraphs: [...get().streamedParagraphs, paragraph] }),
      setCarouselState: (carouselResult, carouselSvgs, carouselSvgsVisible) =>
        set({ carouselResult, carouselSvgs, carouselSvgsVisible }),
      setCarouselVisibleCount: (carouselSvgsVisible) => set({ carouselSvgsVisible }),
      setVersionTimeline: (versionTimeline) => set({ versionTimeline }),
      markStage: (id, status, detail, ms) =>
        set({
          stages: get().stages.map((s) =>
            s.id === id ? { ...s, status, detail, ms: ms ?? s.ms } : s,
          ),
        }),
    }),
    {
      name: "scholarflow-workflow",
      partialize: (s) => ({
        lastGenerate: s.lastGenerate,
        draftVersions: s.draftVersions,
        versionTimeline: s.versionTimeline,
        theme: s.theme,
        carouselResult: s.carouselResult,
        carouselSvgs: s.carouselSvgs,
      }),
    },
  ),
);

export { defaultStages };
