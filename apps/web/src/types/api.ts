export type AiModels = {
  ollama_model: string;
  writer_model: string;
  humanizer_model: string;
  critic_model: string;
  predictor_model: string;
};

export type AiStatus = {
  connected: boolean;
  online: boolean;
  provider: string;
  writer: string;
  humanizer?: string;
  critic: string;
  predictor: string;
  models: string[];
  installed_models: string[];
  detail: string;
  default_model: string;
  missing_models?: string[];
  errors?: Array<{ error: string; message: string; resolution?: string }>;
};

export type ContentModes = {
  modes: Record<
    string,
    {
      label: string;
      tone: string;
      emphasis: string[];
      avoid: string[];
      opening_guidance: string;
    }
  >;
  default_mode: string;
};

export type PostSummary = {
  id: string;
  topic: string;
  format: string;
  content_mode: string;
  status: string;
  body: string;
  critic_scores: Record<string, unknown> | null;
  engagement_prediction: Record<string, unknown> | null;
  created_at: string | null;
};

export type PostDetail = {
  id: string;
  topic: string;
  format: string;
  content_mode: string;
  status: string;
  body: string;
  critic_scores: Record<string, unknown> | null;
  engagement_prediction: Record<string, unknown> | null;
  tags: string[];
};

export type EvidenceItem = {
  id: string;
  source: string;
  date: string | null;
  confidence: number | null;
  extracted_claim: string | null;
};

export type ResearchSource = {
  id?: string;
  title: string;
  url: string;
  tier: number;
  score?: number;
  source_type?: string;
  snippet?: string;
};

export type ResearchEvidence = {
  claim: string;
  supporting_sources: string[];
  contradicting_sources: string[];
  confidence: number;
  last_verified: string;
  verified: boolean;
};

export type ResearchShape = {
  topic: string;
  sources: ResearchSource[];
  evidence: ResearchEvidence[];
  trends: Array<{
    trend: string;
    momentum: number;
    confidence: number;
    source_count: number;
    supporting_sources: string[];
  }>;
  summary: string;
  open_questions: string[];
  connector_stats: Record<string, number>;
  offline: boolean;
  key_findings?: string[];
  status?: string;
};

export type GenerateRequest = {
  topic: string;
  content_mode?: string;
  format?: string;
  audience?: string;
  selected_angle_index?: number;
  save?: boolean;
};

export type GenerateResponse = {
  pipeline_run_id: string;
  post_id?: string;
  topic: string;
  content_mode: string;
  format: string;
  audience: string;
  research: ResearchShape;
  content_opportunity: Record<string, unknown>;
  trends: Record<string, unknown>;
  insight: Record<string, unknown>;
  angles: Record<string, unknown>[];
  selected_angle: Record<string, unknown>;
  strategy: Record<string, unknown>;
  draft: string;
  debate: Record<string, unknown> | null;
  grounded_draft: string;
  final_text: string;
  safe: boolean;
  approval_allowed: boolean;
  status: string;
  quality_score: Record<string, unknown>;
  rewrite_loop: Record<string, unknown> | null;
  model_routing: Record<string, unknown>;
  grounding: {
    approved_claims: Array<{ text: string; claim_type: string; reason: string }>;
    rejected_claims: Array<{ text: string; claim_type: string; reason: string }>;
    warnings: string[];
  };
  writing_quality: Record<string, unknown>;
  critic: { scores: Record<string, unknown>; issues: string[] };
  engagement_prediction: Record<string, unknown>;
  stages: Record<string, unknown>;
};

export type KnowledgeGraphData = {
  nodes: Array<{
    id: string;
    type: string;
    label: string;
    properties: Record<string, unknown>;
  }>;
  edges: Array<{
    id: string;
    source: string;
    target: string;
    relation: string;
    properties: Record<string, unknown>;
  }>;
};

export type PipelineStageId =
  | "research"
  | "reasoning"
  | "writing"
  | "claim_check"
  | "humanizer"
  | "optimizer"
  | "editorial"
  | "carousel"
  | "export";

export type PipelineStageState = {
  id: PipelineStageId;
  label: string;
  status: "pending" | "running" | "completed" | "error" | "skipped";
  ms?: number;
  detail?: string;
};
