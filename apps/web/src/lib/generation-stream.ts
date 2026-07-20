import type {
  GenerateRequest,
  GenerateResponse,
  PipelineStageId,
  ResearchEvidence,
  ResearchSource,
} from "@/types/api";

export const STREAM_MILESTONES: Array<{ stage: PipelineStageId; label: string }> = [
  { stage: "research", label: "Research Complete" },
  { stage: "reasoning", label: "Reasoning Complete" },
  { stage: "writing", label: "Writing Complete" },
  { stage: "optimizer", label: "Optimization Complete" },
  { stage: "editorial", label: "Editorial Review Complete" },
  { stage: "carousel", label: "Carousel Complete" },
];

export function splitParagraphs(text: string): string[] {
  return text
    .split(/\n\s*\n/)
    .map((p) => p.trim())
    .filter(Boolean);
}

export function buildVersionTimeline(result: GenerateResponse) {
  const at = new Date().toISOString();
  const versions: Array<{ id: string; label: string; text: string; at: string }> = [];
  if (result.draft) {
    versions.push({ id: "v1", label: "v1 — Draft", text: result.draft, at });
  }
  const rewrite = result.rewrite_loop as Record<string, unknown> | null;
  const optimized =
    result.grounded_draft ||
    (typeof rewrite?.output === "string" ? rewrite.output : undefined);
  if (typeof optimized === "string" && optimized && optimized !== result.draft) {
    versions.push({ id: "optimized", label: "Optimization", text: optimized, at });
  }
  if (result.grounded_draft && result.grounded_draft !== result.final_text) {
    versions.push({
      id: "editorial",
      label: "Editorial",
      text: result.grounded_draft,
      at,
    });
  }
  if (result.final_text) {
    versions.push({ id: "final", label: "Final", text: result.final_text, at });
  }
  return versions;
}

export function extractReasoningSections(result: GenerateResponse) {
  const insight = (result.insight || {}) as Record<string, unknown>;
  const strategy = (result.strategy || {}) as Record<string, unknown>;
  const opportunity = (result.content_opportunity || {}) as Record<string, unknown>;
  const angles = result.angles || [];

  const asStrings = (v: unknown): string[] => {
    if (!v) return [];
    if (Array.isArray(v)) return v.map((x) => String(x));
    if (typeof v === "string") return [v];
    return [];
  };

  return {
    assumptions: asStrings(insight.assumptions ?? strategy.assumptions),
    contradictions: asStrings(
      insight.contradictions ?? insight.tensions ?? opportunity.risks,
    ),
    tradeoffs: asStrings(insight.tradeoffs ?? strategy.tradeoffs),
    frameworks: asStrings(insight.frameworks ?? strategy.framework ?? strategy.hook_framework),
    insights: asStrings(
      insight.core_insight ??
        insight.summary ??
        insight.headline ??
        (angles[0] as Record<string, unknown> | undefined)?.title,
    ),
    meta: {
      selected_angle: result.selected_angle,
      strategy,
      opportunity,
    },
  };
}

export type ReplayCallbacks = {
  onStageRunning: (stage: PipelineStageId) => void;
  onMilestone: (label: string) => void;
  onResearchSource: (source: ResearchSource) => void;
  onResearchEvidence: (evidence: ResearchEvidence) => void;
  onResearchSummary: (summary: string) => void;
  onReasoningReady: (sections: ReturnType<typeof extractReasoningSections>) => void;
  onParagraph: (index: number, total: number, paragraph: string) => void;
  onCarouselSvg: (index: number, total: number) => void;
  onComplete: (result: GenerateResponse) => void;
  onError: (stage: PipelineStageId, error: Error) => void;
};

const delay = (ms: number) => new Promise((r) => setTimeout(r, ms));

export async function replayGenerationResult(
  result: GenerateResponse,
  cb: ReplayCallbacks,
  options?: { fromStage?: PipelineStageId; carouselSvgs?: string[] },
) {
  const from = options?.fromStage ?? "research";
  const stages: PipelineStageId[] = [
    "research",
    "reasoning",
    "writing",
    "optimizer",
    "editorial",
    "carousel",
  ];
  const startIdx = Math.max(0, stages.indexOf(from));

  try {
    for (let si = startIdx; si < stages.length; si++) {
      const stage = stages[si];
      cb.onStageRunning(stage);

      if (stage === "research") {
        const sources = result.research?.sources || [];
        for (let i = 0; i < sources.length; i++) {
          cb.onResearchSource(sources[i]);
          await delay(120);
        }
        const evidence = result.research?.evidence || [];
        for (let i = 0; i < evidence.length; i++) {
          cb.onResearchEvidence(evidence[i]);
          await delay(100);
        }
        if (result.research?.summary) {
          await delay(80);
          cb.onResearchSummary(result.research.summary);
        }
        cb.onMilestone("Research Complete");
      }

      if (stage === "reasoning") {
        await delay(200);
        cb.onReasoningReady(extractReasoningSections(result));
        cb.onMilestone("Reasoning Complete");
      }

      if (stage === "writing") {
        const text = result.draft || result.final_text || "";
        const paragraphs = splitParagraphs(text);
        for (let i = 0; i < paragraphs.length; i++) {
          cb.onParagraph(i, paragraphs.length, paragraphs[i]);
          await delay(180);
        }
        cb.onMilestone("Writing Complete");
      }

      if (stage === "optimizer") {
        await delay(240);
        cb.onMilestone("Optimization Complete");
      }

      if (stage === "editorial") {
        await delay(200);
        cb.onMilestone("Editorial Review Complete");
      }

      if (stage === "carousel") {
        const svgs = options?.carouselSvgs || [];
        if (svgs.length) {
          for (let i = 0; i < svgs.length; i++) {
            cb.onCarouselSvg(i, svgs.length);
            await delay(160);
          }
        } else {
          await delay(120);
        }
        cb.onMilestone("Carousel Complete");
      }
    }

    cb.onMilestone("Final");
    cb.onComplete(result);
  } catch (e) {
    const err = e instanceof Error ? e : new Error("Replay failed");
    const failed = stages[startIdx] ?? "research";
    cb.onError(failed, err);
    throw err;
  }
}

export type RunGenerationOptions = {
  request: GenerateRequest;
  generate: (req: GenerateRequest) => Promise<GenerateResponse>;
  runCarousel?: (payload: { topic: string; draft?: string }) => Promise<Record<string, unknown>>;
  fromStage?: PipelineStageId;
  cachedResult?: GenerateResponse;
  cachedCarouselSvgs?: string[];
} & ReplayCallbacks;

export async function runGenerationWithReplay(opts: RunGenerationOptions) {
  const {
    request,
    generate,
    runCarousel,
    fromStage,
    cachedResult,
    cachedCarouselSvgs,
    ...cb
  } = opts;

  let result = cachedResult;
  if (!result) {
    cb.onStageRunning("research");
    result = await generate(request);
  }

  let carouselSvgs = cachedCarouselSvgs;
  let carouselPayload: Record<string, unknown> | null = null;
  if (!carouselSvgs && runCarousel && result.final_text) {
    try {
      cb.onStageRunning("carousel");
      carouselPayload = await runCarousel({
        topic: result.topic,
        draft: result.final_text,
      });
      carouselSvgs = (carouselPayload.svgs as string[]) || [];
    } catch {
      carouselSvgs = [];
    }
  }

  await replayGenerationResult(result, cb, {
    fromStage: cachedResult ? fromStage ?? "research" : fromStage,
    carouselSvgs,
  });

  return { result, carouselSvgs: carouselSvgs || [], carouselResult: carouselPayload };
}
