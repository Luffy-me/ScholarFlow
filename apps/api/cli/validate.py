"""Run real Ollama generation with Truth Layer v2 grounding metrics."""

from __future__ import annotations

import argparse
import asyncio
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from apps.api.config import settings
from apps.api.pipeline import run_generation_pipeline
from apps.api.providers import build_base_provider
from models.ollama import OllamaUnavailableError
from shared.knowledge import repo_path
from shared.quality import scan_text


def evaluate_text(text: str, *, safe: bool) -> dict[str, Any]:
    scan = scan_text(text)
    authenticity = 100
    if scan.has_generic_ai:
        authenticity -= 35
    if scan.has_weak_hook:
        authenticity -= 15
    if not scan.has_strong_first_person:
        authenticity -= 25
    if scan.first_person_count == 0:
        authenticity -= 20
    if not safe:
        authenticity -= 40
    authenticity = max(0, min(100, authenticity))
    return {
        "authenticity_score": authenticity,
        "first_person": scan.has_strong_first_person,
        "first_person_count": scan.first_person_count,
        "generic_ai_patterns": scan.has_generic_ai,
        "weak_hook": scan.has_weak_hook,
        "hallucination_risk": "high" if not safe else "low",
        "fake_experience": scan.has_fake_experience,
        "grounding_safe": safe,
    }


async def run_dataset(limit: int | None = None) -> dict[str, Any]:
    dataset_path = repo_path("examples/test_topics.json")
    dataset = json.loads(dataset_path.read_text(encoding="utf-8"))
    topics = dataset.get("topics", [])
    # Prefer one topic per category for compact validation runs.
    seen: set[str] = set()
    deduped: list[dict[str, Any]] = []
    for item in topics:
        cat = str(item.get("category", ""))
        if cat in seen:
            continue
        seen.add(cat)
        deduped.append(item)
    topics = deduped
    if limit is not None:
        topics = topics[:limit]
    provider = build_base_provider(fake=False)
    try:
        status = await provider.ensure_available()  # type: ignore[attr-defined]
    except OllamaUnavailableError as exc:
        return {"error": str(exc), "results": []}

    results: list[dict[str, Any]] = []
    for item in topics:
        print(f"Generating: {item['id']} — {item['topic'][:60]}...", flush=True)
        generated = await run_generation_pipeline(
            None,
            topic=item["topic"],
            content_mode=item.get("content_mode", "founder"),
            format=item.get("format", "short"),
            audience=item.get("audience", ""),
            fake=False,
        )
        quality = evaluate_text(generated.get("final_text", ""), safe=bool(generated.get("safe")))
        results.append(
            {
                "id": item["id"],
                "category": item.get("category"),
                "topic": item["topic"],
                "content_mode": item.get("content_mode"),
                "audience": item.get("audience"),
                "draft": generated.get("draft"),
                "grounded_draft": generated.get("grounded_draft"),
                "humanized": generated.get("final_text"),
                "safe": generated.get("safe"),
                "approval_allowed": generated.get("approval_allowed"),
                "grounding": generated.get("grounding"),
                "critic": generated.get("critic"),
                "engagement_prediction": generated.get("engagement_prediction"),
                "quality_eval": quality,
            }
        )
        print(
            json.dumps(
                {
                    "id": item["id"],
                    "safe": generated.get("safe"),
                    "approval_allowed": generated.get("approval_allowed"),
                    **quality,
                },
                indent=2,
            ),
            flush=True,
        )

    summary = {
        "model_writer": settings.model_for_stage("writer"),
        "model_critic": settings.model_for_stage("critic"),
        "model_predictor": settings.model_for_stage("predictor"),
        "ollama_models": status.models,
        "count": len(results),
        "avg_authenticity": round(
            sum(r["quality_eval"]["authenticity_score"] for r in results) / max(len(results), 1), 1
        ),
        "first_person_rate": round(
            sum(1 for r in results if r["quality_eval"]["first_person"]) / max(len(results), 1), 2
        ),
        "generic_ai_rate": round(
            sum(1 for r in results if r["quality_eval"]["generic_ai_patterns"]) / max(len(results), 1), 2
        ),
        "grounding_safe_rate": round(sum(1 for r in results if r.get("safe")) / max(len(results), 1), 2),
        "approval_allowed_rate": round(
            sum(1 for r in results if r.get("approval_allowed")) / max(len(results), 1), 2
        ),
    }
    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "truth_layer": "v2",
        "summary": summary,
        "results": results,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Run Phase 1.5/Truth Layer v2 validation dataset")
    parser.add_argument("--limit", type=int, default=4, help="Topic limit (category-deduped when <=4)")
    parser.add_argument(
        "--out",
        default="examples/validation_report_v2.json",
        help="Output report path",
    )
    args = parser.parse_args()
    report = asyncio.run(run_dataset(limit=args.limit))
    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report.get("summary", report), indent=2))
    print(f"Wrote {out_path}")
    return 0 if "error" not in report else 2


if __name__ == "__main__":
    raise SystemExit(main())
