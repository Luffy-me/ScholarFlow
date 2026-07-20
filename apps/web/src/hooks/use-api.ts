"use client";

import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api";

export function useAiStatus() {
  return useQuery({ queryKey: ["ai-status"], queryFn: api.status, refetchInterval: 20_000 });
}

export function useAiModels() {
  return useQuery({ queryKey: ["ai-models"], queryFn: api.models });
}

export function useModes() {
  return useQuery({ queryKey: ["modes"], queryFn: api.modes });
}

export function usePosts() {
  return useQuery({ queryKey: ["posts"], queryFn: api.posts });
}

export function usePost(id?: string) {
  return useQuery({
    queryKey: ["post", id],
    queryFn: () => api.post(id!),
    enabled: Boolean(id),
  });
}

export function useEvidence(postId?: string) {
  return useQuery({
    queryKey: ["evidence", postId],
    queryFn: () => api.evidence(postId!),
    enabled: Boolean(postId),
  });
}

export function useMemory() {
  return useQuery({ queryKey: ["memory"], queryFn: api.memory });
}

export function useKnowledgeGraph() {
  return useQuery({ queryKey: ["knowledge-graph"], queryFn: api.knowledgeGraph });
}

export function useEvidenceGraph() {
  return useQuery({ queryKey: ["evidence-graph"], queryFn: api.evidenceGraph });
}
