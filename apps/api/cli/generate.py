"""CLI: generate a LinkedIn post via the local Ollama pipeline.

Usage:
  python -m apps.api.cli.generate --topic "local AI eval loops" --mode founder --audience "technical founders"
"""

from __future__ import annotations

import argparse
import asyncio
import json
import sys
from typing import Any

from apps.api.config import settings
from apps.api.pipeline import run_generation_pipeline
from models.fake import FakeProvider
from models.ollama import OllamaProvider, OllamaUnavailableError
from shared.quality import scan_text


def build_provider(*, fake: bool = False) -> Any:
    if fake or settings.use_fake_provider:
        return FakeProvider()
    return OllamaProvider(
        base_url=settings.ollama_base_url,
        default_model=settings.ollama_model,
        think=settings.ollama_think,
        num_ctx=settings.ollama_num_ctx,
    )


def _print_report(result: dict[str, Any]) -> None:
    critic = result.get("critic", {})
    engagement = result.get("engagement_prediction", {})
    scan = scan_text(result.get("final_text", ""))

    print("=" * 72)
    print("LINKEDIN CONTENT INTELLIGENCE — GENERATION REPORT")
    print("=" * 72)
    print(f"Topic:        {result.get('topic')}")
    print(f"Content mode: {result.get('content_mode')}")
    print(f"Audience:     {result.get('audience') or '(none)'}")
    print(f"Model:        {settings.ollama_model}")
    print("-" * 72)
    print("GENERATED POST (writer draft)")
    print("-" * 72)
    print(result.get("draft", "").strip())
    print()
    print("-" * 72)
    print("HUMANIZED VERSION")
    print("-" * 72)
    print(result.get("final_text", "").strip())
    print()
    print("-" * 72)
    print("CRITIC SCORE")
    print("-" * 72)
    print(json.dumps(critic.get("scores", {}), indent=2))
    if critic.get("issues"):
        print("Issues:")
        for issue in critic["issues"]:
            print(f"  - {issue}")
    print()
    print("-" * 72)
    print("ENGAGEMENT PREDICTION SCORE")
    print("-" * 72)
    print(json.dumps(engagement, indent=2))
    print()
    print("-" * 72)
    print("QUICK QUALITY SCAN (deterministic)")
    print("-" * 72)
    print(
        json.dumps(
            {
                "first_person": scan.has_strong_first_person,
                "first_person_count": scan.first_person_count,
                "generic_ai": scan.has_generic_ai,
                "weak_hook": scan.has_weak_hook,
                "fake_experience": scan.has_fake_experience,
                "hallucination_risk": "high" if scan.has_fake_experience else "low",
            },
            indent=2,
        )
    )
    print("=" * 72)


async def _async_main(args: argparse.Namespace) -> int:
    provider = build_provider(fake=args.fake)
    if not args.fake:
        try:
            status = await provider.ensure_available()
            print(f"Ollama online. Models: {', '.join(status.models) or 'none'}")
            print(f"Using model: {settings.ollama_model}")
        except OllamaUnavailableError as exc:
            print(f"ERROR: {exc}", file=sys.stderr)
            return 2

    result = await run_generation_pipeline(
        provider,
        topic=args.topic,
        content_mode=args.mode,
        format=args.format,
        audience=args.audience,
    )
    _print_report(result)

    if args.json_out:
        with open(args.json_out, "w", encoding="utf-8") as handle:
            json.dump(result, handle, indent=2)
            handle.write("\n")
        print(f"Wrote JSON report to {args.json_out}")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Generate LinkedIn content via local Ollama pipeline")
    parser.add_argument("--topic", required=True, help="Post topic")
    parser.add_argument("--mode", default="founder", help="Content mode (founder/researcher/engineer/career_journey)")
    parser.add_argument("--audience", default="", help="Target audience")
    parser.add_argument("--format", default="short", help="Post format")
    parser.add_argument("--fake", action="store_true", help="Use FakeProvider instead of Ollama")
    parser.add_argument("--json-out", default="", help="Optional path to write full JSON result")
    args = parser.parse_args(argv)
    return asyncio.run(_async_main(args))


if __name__ == "__main__":
    raise SystemExit(main())
