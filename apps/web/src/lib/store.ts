"use client";

import { create } from "zustand";
import { persist } from "zustand/middleware";
import type { GenerateResponse, PipelineStageState } from "@/types/api";

type WorkflowState = {
  lastGenerate: GenerateResponse | null;
  stages: PipelineStageState[];
  draftVersions: Array<{ id: string; text: string; at: string; label: string }>;
  theme: "light" | "dark" | "system";
  inspectorOpen: boolean;
  setTheme: (theme: "light" | "dark" | "system") => void;
  setInspectorOpen: (open: boolean) => void;
  setLastGenerate: (value: GenerateResponse | null) => void;
  setStages: (stages: PipelineStageState[]) => void;
  pushVersion: (text: string, label: string) => void;
  restoreVersion: (id: string) => string | null;
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
  { id: "export", label: "Export", status: "pending" },
];

export const useWorkflowStore = create<WorkflowState>()(
  persist(
    (set, get) => ({
      lastGenerate: null,
      stages: defaultStages,
      draftVersions: [],
      theme: "system",
      inspectorOpen: true,
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
    }),
    {
      name: "scholarflow-workflow",
      partialize: (s) => ({
        lastGenerate: s.lastGenerate,
        draftVersions: s.draftVersions,
        theme: s.theme,
      }),
    },
  ),
);

export { defaultStages };
