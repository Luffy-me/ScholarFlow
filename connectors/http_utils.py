"""Shared HTTP helpers for real connectors (local-first, short timeouts)."""

from __future__ import annotations

import os
import xml.etree.ElementTree as ET
from typing import Any

import httpx

DEFAULT_TIMEOUT = float(os.getenv("ACQUISITION_HTTP_TIMEOUT", "8"))
USER_AGENT = os.getenv(
    "ACQUISITION_USER_AGENT",
    "LinkedInContentIntelligence/0.1 (+local-research; offline-capable)",
)


def network_enabled() -> bool:
    """Network is on by default; set ACQUISITION_OFFLINE=1 to force fixtures."""
    return os.getenv("ACQUISITION_OFFLINE", "").strip() not in {"1", "true", "yes"}


async def fetch_text(
    url: str,
    *,
    params: dict[str, Any] | None = None,
    timeout: float = DEFAULT_TIMEOUT,
) -> str | None:
    if not network_enabled():
        return None
    try:
        async with httpx.AsyncClient(
            timeout=timeout,
            headers={"User-Agent": USER_AGENT, "Accept": "*/*"},
            follow_redirects=True,
        ) as client:
            response = await client.get(url, params=params)
            if response.status_code >= 400:
                return None
            return response.text
    except Exception:  # noqa: BLE001
        return None


async def fetch_json(
    url: str,
    *,
    params: dict[str, Any] | None = None,
    timeout: float = DEFAULT_TIMEOUT,
) -> Any | None:
    if not network_enabled():
        return None
    try:
        async with httpx.AsyncClient(
            timeout=timeout,
            headers={"User-Agent": USER_AGENT, "Accept": "application/json"},
            follow_redirects=True,
        ) as client:
            response = await client.get(url, params=params)
            if response.status_code >= 400:
                return None
            return response.json()
    except Exception:  # noqa: BLE001
        return None


def parse_rss_items(xml_text: str, *, limit: int = 10) -> list[dict[str, str]]:
    """Parse RSS/Atom XML into dict items without third-party feed parsers."""
    if not xml_text.strip():
        return []
    try:
        root = ET.fromstring(xml_text)
    except ET.ParseError:
        return []

    ns = {
        "atom": "http://www.w3.org/2005/Atom",
        "dc": "http://purl.org/dc/elements/1.1/",
        "content": "http://purl.org/rss/1.0/modules/content/",
    }
    items: list[dict[str, str]] = []

    # RSS 2.0
    for item in root.findall(".//item"):
        title = (item.findtext("title") or "").strip()
        link = (item.findtext("link") or "").strip()
        desc = (item.findtext("description") or item.findtext("content:encoded", default="", namespaces=ns) or "").strip()
        author = (
            item.findtext("author")
            or item.findtext("dc:creator", default="", namespaces=ns)
            or ""
        ).strip()
        published = (item.findtext("pubDate") or item.findtext("dc:date", default="", namespaces=ns) or "").strip()
        if title or link:
            items.append(
                {
                    "title": title or link,
                    "url": link,
                    "snippet": _strip_html(desc)[:400],
                    "content": _strip_html(desc),
                    "author": author,
                    "published_at": published,
                }
            )
        if len(items) >= limit:
            return items

    # Atom
    for entry in root.findall(".//atom:entry", ns) or root.findall(".//{http://www.w3.org/2005/Atom}entry"):
        title = (entry.findtext("atom:title", default="", namespaces=ns) or entry.findtext("{http://www.w3.org/2005/Atom}title") or "").strip()
        link_el = entry.find("atom:link", ns) or entry.find("{http://www.w3.org/2005/Atom}link")
        link = ""
        if link_el is not None:
            link = (link_el.attrib.get("href") or "").strip()
        summary = (
            entry.findtext("atom:summary", default="", namespaces=ns)
            or entry.findtext("{http://www.w3.org/2005/Atom}summary")
            or entry.findtext("atom:content", default="", namespaces=ns)
            or ""
        ).strip()
        published = (
            entry.findtext("atom:updated", default="", namespaces=ns)
            or entry.findtext("{http://www.w3.org/2005/Atom}updated")
            or ""
        ).strip()
        if title or link:
            items.append(
                {
                    "title": title or link,
                    "url": link,
                    "snippet": _strip_html(summary)[:400],
                    "content": _strip_html(summary),
                    "author": "",
                    "published_at": published,
                }
            )
        if len(items) >= limit:
            break
    return items


def _strip_html(value: str) -> str:
    return re_sub_tags(value)


def re_sub_tags(value: str) -> str:
    import re as _re

    text = _re.sub(r"<[^>]+>", " ", value or "")
    return _re.sub(r"\s+", " ", text).strip()
