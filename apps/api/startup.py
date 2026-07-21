"""Startup validation and runtime directory setup."""

from __future__ import annotations

import logging
from pathlib import Path

from sqlalchemy import text

from apps.api.config import settings
from apps.api.ollama_probe import missing_models, probe_ollama, resolution_for_missing
from database.session import create_db_engine, init_db
from shared.knowledge import repo_path

logger = logging.getLogger(__name__)


def ensure_runtime_directories() -> None:
    paths = [
        settings.research_sources_dir,
        "feedback",
        "knowledge",
        "knowledge_graph",
        ".scholarflow",
    ]
    for rel in paths:
        p = repo_path(rel)
        p.mkdir(parents=True, exist_ok=True)
        logger.debug("Ensured directory: %s", p)


def validate_database() -> bool:
    try:
        init_db(settings.database_url)
        with create_db_engine(settings.database_url).connect() as conn:
            conn.execute(text("SELECT 1"))
        logger.info("✓ Database available (%s)", settings.database_url.split("///")[-1][:40])
        return True
    except Exception as exc:  # noqa: BLE001
        logger.error("✗ Database unavailable: %s", exc)
        return False


async def validate_ollama_and_models() -> None:
    if settings.use_fake_provider:
        logger.info("USE_FAKE_PROVIDER=true — skipping Ollama validation")
        return

    writer = settings.model_for_stage("writer")
    critic = settings.model_for_stage("critic")
    predictor = settings.model_for_stage("predictor")

    probe = await probe_ollama(settings.ollama_base_url)
    if not probe.reachable:
        logger.warning(
            "✗ Ollama not available at %s — %s (%s)",
            settings.ollama_base_url,
            probe.message,
            probe.resolution,
        )
        return

    logger.info("✓ Ollama available at %s (%d models)", settings.ollama_base_url, len(probe.installed_models))

    for label, model in (
        ("Writer", writer),
        ("Critic", critic),
        ("Predictor", predictor),
    ):
        if missing_models(probe.installed_models, [model]):
            logger.warning("  ✗ %s: %s — %s", label, model, resolution_for_missing(model))
        else:
            logger.info("  ✓ %s: %s", label, model)


async def run_startup_validation() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
    )
    logger.info("ScholarFlow API startup validation")
    ensure_runtime_directories()
    validate_database()
    await validate_ollama_and_models()
