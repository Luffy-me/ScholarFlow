"use client";

import { useEffect, useState } from "react";
import { toast } from "sonner";
import { useAiModels, useAiStatus, useMemory } from "@/hooks/use-api";
import { useWorkflowStore } from "@/lib/store";
import { api } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Card, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Textarea } from "@/components/ui/textarea";

export default function SettingsPage() {
  const { data: models } = useAiModels();
  const { data: status } = useAiStatus();
  const { data: memory } = useMemory();
  const { theme, setTheme } = useWorkflowStore();
  const [memoryJson, setMemoryJson] = useState("");
  const [cleanupHours, setCleanupHours] = useState("24");

  useEffect(() => {
    if (memory) setMemoryJson(JSON.stringify(memory, null, 2));
  }, [memory]);

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-semibold tracking-tight">Settings</h1>
        <p className="text-sm text-[var(--muted-foreground)]">Models, storage, theme — wired to existing backend APIs.</p>
      </div>

      <div className="grid gap-4 xl:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle>Model selection</CardTitle>
            <Badge tone={status?.online ? "success" : "warning"}>
              {status?.online ? "online" : "offline"}
            </Badge>
          </CardHeader>
          <div className="space-y-2 text-sm">
            <div>Provider: {status?.provider || "—"}</div>
            <div>Default: {status?.default_model || models?.ollama_model || "—"}</div>
            <div className="rounded-xl bg-[var(--muted)] p-3 text-xs">
              <div>Qwen / writer: {models?.writer_model}</div>
              <div>Humanizer: {models?.humanizer_model}</div>
              <div>DeepSeek / critic: {models?.critic_model}</div>
              <div>Predictor: {models?.predictor_model}</div>
              <div>Ollama: {models?.ollama_model}</div>
            </div>
            <CardDescription>
              Model parameters are controlled by backend env (`WRITER_MODEL`, `DEEPSEEK_MODEL`, etc.).
            </CardDescription>
          </div>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Theme</CardTitle>
          </CardHeader>
          <div className="flex gap-2">
            {(["light", "dark", "system"] as const).map((t) => (
              <Button key={t} variant={theme === t ? "default" : "outline"} onClick={() => setTheme(t)}>
                {t}
              </Button>
            ))}
          </div>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Storage & cleanup</CardTitle>
          </CardHeader>
          <label className="block space-y-1.5 text-sm">
            <span>Raw download TTL (hours)</span>
            <input
              className="flex h-10 w-full rounded-xl border border-[var(--border)] bg-[var(--card)] px-3 text-sm"
              value={cleanupHours}
              onChange={(e) => setCleanupHours(e.target.value)}
            />
          </label>
          <CardDescription className="mt-2">
            Acquisition cleanup defaults to 24h in the backend storage manager (`ACQUISITION_*` env).
          </CardDescription>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Google Drive backup</CardTitle>
          </CardHeader>
          <CardDescription>
            Backend supports Drive mirror via `ACQUISITION_GDRIVE_DIR` — point it at a sync folder. No cloud API
            dependency.
          </CardDescription>
          <Button
            className="mt-3"
            variant="outline"
            onClick={() => toast.message("Configure ACQUISITION_GDRIVE_DIR on the API host")}
          >
            View backup instructions
          </Button>
        </Card>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>User memory</CardTitle>
          <CardDescription>GET/PUT `/api/v1/memory`</CardDescription>
        </CardHeader>
        <Textarea rows={16} value={memoryJson} onChange={(e) => setMemoryJson(e.target.value)} />
        <Button
          className="mt-3"
          onClick={async () => {
            try {
              const parsed = JSON.parse(memoryJson);
              await api.updateMemory(parsed);
              toast.success("Memory updated");
            } catch (e) {
              toast.error(e instanceof Error ? e.message : "Invalid memory JSON");
            }
          }}
        >
          Save memory
        </Button>
      </Card>
    </div>
  );
}
