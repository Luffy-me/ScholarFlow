import type {
  AiModels,
  AiStatus,
  ContentModes,
  EvidenceItem,
  GenerateRequest,
  GenerateResponse,
  KnowledgeGraphData,
  PostDetail,
  PostSummary,
} from "@/types/api";

const BASE = "/backend";

export type ApiErrorBody = {
  error?: string;
  message?: string;
  resolution?: string;
};

export function formatApiError(body: unknown, fallback: string): string {
  if (!body || typeof body !== "object") return fallback;
  const b = body as ApiErrorBody;
  const parts = [b.message || b.error || fallback];
  if (b.resolution) parts.push(b.resolution);
  return parts.filter(Boolean).join(" — ");
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE}${path}`, {
    ...init,
    headers: {
      "Content-Type": "application/json",
      ...(init?.headers || {}),
    },
    cache: "no-store",
  });
  if (!res.ok) {
    let detail = res.statusText;
    try {
      const body = await res.json();
      if (typeof body?.detail === "string") {
        detail = body.detail;
      } else if (body?.detail && typeof body.detail === "object") {
        detail = formatApiError(body.detail, detail);
      } else {
        detail = formatApiError(body, detail);
      }
    } catch {
      /* ignore */
    }
    throw new Error(detail || `Request failed (${res.status})`);
  }
  return res.json() as Promise<T>;
}

export const api = {
  health: () => request<{ status: string }>("/health"),
  models: () => request<AiModels>("/api/v1/ai/models"),
  status: () => request<AiStatus>("/api/v1/ai/status"),
  modes: () => request<ContentModes>("/api/v1/modes"),
  memory: () => request<Record<string, unknown>>("/api/v1/memory"),
  updateMemory: (memory: Record<string, unknown>) =>
    request<Record<string, unknown>>("/api/v1/memory", {
      method: "PUT",
      body: JSON.stringify({ memory }),
    }),
  posts: () => request<PostSummary[]>("/api/v1/posts"),
  post: (id: string) => request<PostDetail>(`/api/v1/posts/${id}`),
  updatePost: (id: string, payload: { body?: string; status?: string; title?: string; tags?: string[] }) =>
    request<{ id: string; status: string; body: string }>(`/api/v1/posts/${id}`, {
      method: "PATCH",
      body: JSON.stringify(payload),
    }),
  generate: (payload: GenerateRequest) =>
    request<GenerateResponse>("/api/v1/generate", {
      method: "POST",
      body: JSON.stringify(payload),
    }),
  evidence: (postId: string) => request<EvidenceItem[]>(`/api/v1/posts/${postId}/evidence`),
  addEvidence: (
    postId: string,
    payload: {
      source: string;
      extracted_claim: string;
      date?: string | null;
      confidence?: number | null;
      url?: string | null;
      title?: string | null;
    },
  ) =>
    request<{ id: string; post_id: string }>(`/api/v1/posts/${postId}/evidence`, {
      method: "POST",
      body: JSON.stringify(payload),
    }),
  knowledgeGraph: () => fetch("/api/local/knowledge/graph").then(async (r) => {
    if (!r.ok) throw new Error("Failed to load knowledge graph");
    return r.json() as Promise<KnowledgeGraphData>;
  }),
  evidenceGraph: () => fetch("/api/local/knowledge/evidence").then(async (r) => {
    if (!r.ok) throw new Error("Failed to load evidence graph");
    return r.json() as Promise<{ claims: Array<Record<string, unknown>> }>;
  }),
  runCarousel: (payload: { topic: string; draft?: string; theme?: string }) =>
    fetch("/api/local/carousel", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    }).then(async (r) => {
      if (!r.ok) {
        const err = await r.json().catch(() => ({}));
        throw new Error(err.error || "Carousel generation failed");
      }
      return r.json() as Promise<Record<string, unknown>>;
    }),
};
