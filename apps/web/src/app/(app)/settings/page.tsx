"use client";

import { useEffect, useState } from "react";
import { toast } from "sonner";
import { useAiModels, useAiStatus } from "@/hooks/use-api";
import { useMemory } from "@/hooks/use-api";
import { useWorkflowStore } from "@/lib/store";
import { api } from "@/lib/api";
import { aiConnected, primaryAiIssue } from "@/lib/ai-status";
import { Button } from "@/components/ui/button";
import { Card, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Textarea } from "@/components/ui/textarea";

export default function SettingsPage() {
  const { data: models } = useAiModels();
  const { data: status, isError } = useAiStatus();
  const { data: memory } = useMemory();
  const { theme, setTheme } = useWorkflowStore();
  const [memoryJson, setMemoryJson] = useState("");
  const [cleanupHours, setCleanupHours] = useState("24");

  const connected = aiConnected(status);
  const issue = primaryAiIssue(status);
  const installed = status?.installed_models ?? status?.models ?? [];

  useEffect(() => {
    if (memory) setMemoryJson(JSON.stringify(memory, null, 2));
  }, [memory]);

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-semibold tracking-tight">Settings</h1>
        <p className="text-sm text-[var(--muted-foreground)]">Models and AI connectivity via FastAPI (never direct Ollama).</p>
      </div>

      <div className="grid gap-4 xl:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle>AI / Ollama</CardTitle>
            <Badge tone={isError ? "danger" : connected ? "success" : "warning"}>
              {isError ? "API offline" : connected ? "Connected" : "Offline"}
            </Badge>
          </CardHeader>
          <div className="space-y-3 text-sm">
            {isError ? (
              <p className="text-[var(--danger)]">
                Cannot reach FastAPI. Start:{" "}
                <code className="text-xs">python3 -m uvicorn apps.api.main:app --reload --port 8000</code>
              </p>
            ) : null}
            {!isError && !connected && issue ? (
              <div className="rounded-xl border border-[var(--warning)]/40 bg-[var(--warning)]/5 px-3 py-2 text-sm">
                <div>{issue.message}</div>
                {issue.resolution ? (
                  <div className="mt-1 font-mono text-xs text-[var(--muted-foreground)]">{issue.resolution}</div>
                ) : null}
              </div>
            ) : null}
            <div className="rounded-xl bg-[var(--muted)] p-3 text-xs space-y-1">
              <div>Writer: {status?.writer || models?.writer_model}</div>
              <div>Humanizer: {status?.humanizer || models?.humanizer_model}</div>
              <div>Critic: {status?.critic || models?.critic_model}</div>
              <div>Predictor: {status?.predictor || models?.predictor_model}</div>
            </div>
            <div>
              <div className="mb-1 text-xs font-medium uppercase text-[var(--muted-foreground)]">Installed models</div>
              {installed.length ? (
                <ul className="max-h-32 overflow-auto sf-scrollbar text-xs font-mono">
                  {installed.map((m) => (
                    <li key={m}>{m}</li>
                  ))}
                </ul>
              ) : (
                <CardDescription>No models reported — is Ollama running?</CardDescription>
              )}
            </div>
            <CardDescription>
              Configure via <code className="text-xs">.env</code> (see <code className="text-xs">.env.example</code>). Pull
              models: <code className="text-xs">ollama pull qwen3:8b</code> and{" "}
              <code className="text-xs">ollama pull deepseek-r1:8b</code>.
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
