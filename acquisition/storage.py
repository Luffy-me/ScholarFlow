"""Storage Manager — research cache, knowledge storage, cleanup, optional Drive backup."""

from __future__ import annotations

import json
import os
import shutil
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

from shared.knowledge import ROOT


DEFAULT_ROOT = ROOT / "data" / "acquisition"


class StorageManager:
    """Local-first storage for acquisition artifacts."""

    def __init__(self, root: Path | None = None) -> None:
        self.root = Path(root or os.getenv("ACQUISITION_DATA_DIR") or DEFAULT_ROOT)
        self.research_cache = self.root / "research_cache"
        self.knowledge_dir = self.root / "knowledge"
        self.raw_dir = self.root / "raw_downloads"
        self.backup_dir = self.root / "backups"
        for path in (self.research_cache, self.knowledge_dir, self.raw_dir, self.backup_dir):
            path.mkdir(parents=True, exist_ok=True)

    def cache_key(self, source: str, query: str) -> str:
        safe_source = "".join(c if c.isalnum() or c in "-_" else "_" for c in source)[:64]
        safe_query = "".join(c if c.isalnum() or c in "-_" else "_" for c in query.lower())[:80]
        return f"{safe_source}__{safe_query or 'topic'}.json"

    def write_research_cache(self, source: str, query: str, payload: dict[str, Any]) -> Path:
        path = self.research_cache / self.cache_key(source, query)
        record = {
            "source": source,
            "query": query,
            "cached_at": datetime.now(timezone.utc).isoformat(),
            "payload": payload,
        }
        path.write_text(json.dumps(record, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        return path

    def read_research_cache(self, source: str, query: str, *, max_age_hours: float = 6) -> dict[str, Any] | None:
        path = self.research_cache / self.cache_key(source, query)
        if not path.exists():
            return None
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            return None
        cached_at = data.get("cached_at")
        if cached_at:
            try:
                ts = datetime.fromisoformat(str(cached_at))
                if datetime.now(timezone.utc) - ts > timedelta(hours=max_age_hours):
                    return None
            except ValueError:
                pass
        return data.get("payload") if isinstance(data, dict) else None

    def write_knowledge(self, name: str, payload: dict[str, Any]) -> Path:
        safe = "".join(c if c.isalnum() or c in "-_" else "_" for c in name)[:96]
        path = self.knowledge_dir / f"{safe}.json"
        path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        return path

    def store_raw_download(self, name: str, content: str | bytes, *, suffix: str = ".txt") -> Path:
        stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        safe = "".join(c if c.isalnum() or c in "-_" else "_" for c in name)[:64]
        path = self.raw_dir / f"{stamp}_{safe}{suffix}"
        if isinstance(content, bytes):
            path.write_bytes(content)
        else:
            path.write_text(content, encoding="utf-8")
        return path

    def cleanup_raw_downloads(self, *, max_age_hours: float = 24) -> int:
        """Delete raw downloaded files older than max_age_hours. Returns count removed."""
        cutoff = time.time() - (max_age_hours * 3600)
        removed = 0
        for path in self.raw_dir.glob("*"):
            if not path.is_file():
                continue
            try:
                if path.stat().st_mtime < cutoff:
                    path.unlink(missing_ok=True)
                    removed += 1
            except OSError:
                continue
        return removed

    def cleanup_research_cache(self, *, max_age_hours: float = 72) -> int:
        cutoff = time.time() - (max_age_hours * 3600)
        removed = 0
        for path in self.research_cache.glob("*.json"):
            try:
                if path.stat().st_mtime < cutoff:
                    path.unlink(missing_ok=True)
                    removed += 1
            except OSError:
                continue
        return removed

    def automatic_cleanup(self, *, raw_max_age_hours: float = 24, cache_max_age_hours: float = 72) -> dict[str, int]:
        return {
            "raw_downloads_removed": self.cleanup_raw_downloads(max_age_hours=raw_max_age_hours),
            "research_cache_removed": self.cleanup_research_cache(max_age_hours=cache_max_age_hours),
        }

    def create_local_backup(self, label: str = "acquisition") -> Path:
        stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        archive_base = self.backup_dir / f"{label}_{stamp}"
        archive_path = Path(
            shutil.make_archive(str(archive_base), "zip", root_dir=self.root, base_dir=".")
        )
        return archive_path

    def backup_to_google_drive(
        self,
        *,
        drive_mirror_dir: Path | str | None = None,
        label: str = "acquisition",
    ) -> dict[str, Any]:
        """Optional Google Drive backup.

        Local-first: copies a zip into a mounted Drive folder / mirror path.
        No Google API client is required. Set ACQUISITION_GDRIVE_DIR or pass drive_mirror_dir.
        """
        target = Path(
            drive_mirror_dir
            or os.getenv("ACQUISITION_GDRIVE_DIR")
            or (self.root / "google_drive_mirror")
        )
        target.mkdir(parents=True, exist_ok=True)
        archive = self.create_local_backup(label=label)
        dest = target / archive.name
        shutil.copy2(archive, dest)
        return {
            "ok": True,
            "mode": "local_mirror",
            "archive": str(archive),
            "drive_path": str(dest),
            "note": (
                "Copied backup into Drive mirror directory. "
                "Point ACQUISITION_GDRIVE_DIR at a Google Drive sync folder for cloud upload."
            ),
        }
