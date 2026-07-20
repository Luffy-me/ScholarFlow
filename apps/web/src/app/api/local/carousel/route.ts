import { NextResponse } from "next/server";
import { spawn } from "child_process";
import path from "path";

export const runtime = "nodejs";

/**
 * UI adapter: invokes existing carousel.pipeline without modifying backend agents.
 */
export async function POST(req: Request) {
  const body = await req.json().catch(() => ({}));
  const topic = String(body.topic || "").trim();
  const theme = String(body.theme || "Minimal");
  if (!topic) {
    return NextResponse.json({ error: "topic is required" }, { status: 400 });
  }

  const repoRoot = path.resolve(process.cwd(), "../..");
  const script = `
import json
from carousel.pipeline import CarouselPipeline
result = CarouselPipeline().run(${JSON.stringify(topic)}, theme=${JSON.stringify(theme)})
# Keep payload JSON-serializable / compact for UI
payload = {
  "meta": result.get("meta", {}),
  "review": result.get("review").model_dump() if hasattr(result.get("review"), "model_dump") else result.get("review"),
  "scene_graph": result.get("scene_graph").as_dict() if hasattr(result.get("scene_graph"), "as_dict") else result.get("scene_graph"),
  "svgs": result.get("svgs", [])[:12],
  "exports": result.get("exports", {}),
  "story": result.get("story").model_dump() if hasattr(result.get("story"), "model_dump") else result.get("story"),
}
print(json.dumps(payload, default=str))
`;

  const result = await new Promise<{ ok: boolean; data?: unknown; error?: string }>((resolve) => {
    const child = spawn("python", ["-c", script], { cwd: repoRoot, env: process.env });
    let stdout = "";
    let stderr = "";
    child.stdout.on("data", (d) => {
      stdout += d.toString();
    });
    child.stderr.on("data", (d) => {
      stderr += d.toString();
    });
    child.on("close", (code) => {
      if (code !== 0) {
        resolve({ ok: false, error: stderr || `carousel exited ${code}` });
        return;
      }
      try {
        resolve({ ok: true, data: JSON.parse(stdout.trim().split("\n").pop() || "{}") });
      } catch (e) {
        resolve({ ok: false, error: `Invalid carousel JSON: ${String(e)}\n${stdout}` });
      }
    });
  });

  if (!result.ok) {
    return NextResponse.json({ error: result.error }, { status: 500 });
  }
  return NextResponse.json(result.data);
}
