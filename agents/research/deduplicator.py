"""Deduplicate research documents by URL/title similarity."""

from __future__ import annotations

import re

from connectors.base import SourceDocument


def _norm(text: str) -> str:
    return re.sub(r"\s+", " ", (text or "").strip().lower())


class ResearchDeduplicator:
    name = "research_deduplicator"

    def dedupe(self, documents: list[SourceDocument]) -> list[SourceDocument]:
        seen_urls: set[str] = set()
        seen_titles: set[str] = set()
        unique: list[SourceDocument] = []
        for doc in documents:
            url_key = _norm(doc.url)
            title_key = _norm(doc.title)
            if url_key and url_key in seen_urls:
                continue
            if title_key and title_key in seen_titles:
                continue
            if url_key:
                seen_urls.add(url_key)
            if title_key:
                seen_titles.add(title_key)
            unique.append(doc)
        return unique
