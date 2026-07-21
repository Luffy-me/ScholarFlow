"use client";

export function aiConnected(status?: {
  connected?: boolean;
  online?: boolean;
}): boolean {
  if (!status) return false;
  return Boolean(status.connected ?? status.online);
}

export function primaryAiIssue(status?: {
  errors?: Array<{ message: string; resolution?: string }>;
  detail?: string;
}): { message: string; resolution?: string } | null {
  const first = status?.errors?.[0];
  if (first) {
    return { message: first.message, resolution: first.resolution };
  }
  if (status?.detail && status.detail !== "ok") {
    return { message: status.detail };
  }
  return null;
}
