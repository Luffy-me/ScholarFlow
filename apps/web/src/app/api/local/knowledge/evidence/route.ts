import { NextResponse } from "next/server";
import { promises as fs } from "fs";
import path from "path";

export const runtime = "nodejs";

export async function GET() {
  try {
    const file = path.resolve(process.cwd(), "../../knowledge/evidence/evidence_graph.json");
    const raw = await fs.readFile(file, "utf8");
    return NextResponse.json(JSON.parse(raw));
  } catch (error) {
    return NextResponse.json(
      { claims: [], error: error instanceof Error ? error.message : "unavailable" },
      { status: 200 },
    );
  }
}
