"""Hugging Face Models hub API."""

from __future__ import annotations

from connectors.base import SourceDocument
from connectors.http_utils import fetch_json
from connectors.real_base import RealConnector


async def _live(query: str, limit: int) -> list[SourceDocument]:
    data = await fetch_json(
        "https://huggingface.co/api/models",
        params={
            "search": query or "llm",
            "limit": min(max(limit, 5), 20),
            "sort": "downloads",
            "direction": "-1",
        },
    )
    if not isinstance(data, list):
        return []
    docs: list[SourceDocument] = []
    for row in data:
        model_id = str(row.get("modelId") or row.get("id") or "").strip()
        if not model_id:
            continue
        url = f"https://huggingface.co/{model_id}"
        pipeline = str(row.get("pipeline_tag") or "")
        docs.append(
            SourceDocument(
                id=f"huggingface_models:{model_id}",
                title=model_id,
                url=url,
                snippet=f"{pipeline} downloads={row.get('downloads', 0)} likes={row.get('likes', 0)}",
                content=f"Hugging Face model {model_id}. Pipeline: {pipeline}.",
                author=model_id.split("/")[0] if "/" in model_id else "",
                published_at=str(row.get("lastModified") or "")[:32],
                source_type="huggingface_models",
                tier=1,
                metadata={
                    "downloads": row.get("downloads"),
                    "likes": row.get("likes"),
                    "pipeline_tag": pipeline,
                    "tags": list(row.get("tags") or [])[:12],
                },
            )
        )
        if len(docs) >= limit:
            break
    return docs


class HuggingfaceModelsConnector(RealConnector):
    def __init__(self) -> None:
        super().__init__("huggingface_models", tier=1, live_collect=_live)
