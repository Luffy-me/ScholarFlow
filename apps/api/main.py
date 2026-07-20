"""FastAPI application — Phase 1 AI core (no UI)."""

from __future__ import annotations

import json
import uuid
from pathlib import Path
from typing import Any

from fastapi import Depends, FastAPI, HTTPException
from sqlalchemy.orm import Session

from apps.api.config import settings
from apps.api.pipeline import run_generation_pipeline
from apps.api.schemas.api import (
    EngagementFeedbackCreate,
    EvidenceCreate,
    ExperienceDecision,
    ExperiencePropose,
    GenerateRequest,
    MemoryUpdate,
    PostUpdate,
)
from database.models import (
    EngagementFeedback,
    Feedback,
    GeneratedContent,
    Post,
    PostSource,
    ResearchSource,
    User,
    WritingProfile,
)
from database.session import get_session, init_db
from shared.knowledge import load_content_modes, load_user_memory, repo_path

app = FastAPI(
    title="LinkedIn Content Intelligence Engine",
    version="0.1.0",
    description="Phase 1 AI core API — local-first content intelligence (no UI).",
)


def get_provider():
    from apps.api.providers import build_base_provider

    return build_base_provider(fake=settings.use_fake_provider)


@app.get("/api/v1/ai/models")
def ai_models() -> dict[str, str]:
    return {
        "ollama_model": settings.ollama_model,
        "writer_model": settings.model_for_stage("writer"),
        "humanizer_model": settings.model_for_stage("humanizer"),
        "critic_model": settings.model_for_stage("critic"),
        "predictor_model": settings.model_for_stage("predictor"),
    }



def _ensure_local_user(session: Session) -> User:
    user = session.query(User).filter(User.display_name == "Local User").first()
    if user:
        return user
    memory = load_user_memory()
    user = User(display_name="Local User", preferences={"default_model": settings.default_model})
    session.add(user)
    session.flush()
    profile = WritingProfile(
        user_id=user.id,
        tone=(memory.get("style") or {}).get("tone"),
        allowed_experiences=list(memory.get("experiences") or []) + list(memory.get("projects") or []),
        background=list(memory.get("background") or []),
        skills=list(memory.get("skills") or []),
        projects=list(memory.get("projects") or []),
        preferred_topics=list(memory.get("preferred_topics") or []),
        vocabulary_preferences=list(memory.get("vocabulary_preferences") or []),
        content_preferences=list(memory.get("content_preferences") or []),
        style=dict(memory.get("style") or {}),
        memory_snapshot=memory,
    )
    session.add(profile)
    session.commit()
    session.refresh(user)
    return user


@app.on_event("startup")
def on_startup() -> None:
    init_db(settings.database_url)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/api/v1/ai/status")
async def ai_status() -> dict[str, Any]:
    provider = get_provider()
    status = await provider.health()
    return {
        "online": status.online,
        "provider": status.provider,
        "models": status.models,
        "detail": status.detail,
        "default_model": settings.default_model,
    }


@app.get("/api/v1/modes")
def list_modes() -> dict[str, Any]:
    return load_content_modes()


@app.get("/api/v1/memory")
def get_memory() -> dict[str, Any]:
    from agents.memory_builder import normalize_memory

    return normalize_memory(load_user_memory())


@app.put("/api/v1/memory")
def put_memory(payload: MemoryUpdate) -> dict[str, Any]:
    path = repo_path(settings.user_memory_path)
    path.write_text(json.dumps(payload.memory, indent=2) + "\n", encoding="utf-8")
    from shared.knowledge import clear_knowledge_cache

    clear_knowledge_cache()
    return payload.memory


@app.get("/api/v1/memory/verified")
def get_verified_experiences() -> dict[str, Any]:
    from agents.memory_builder import list_verified_experiences, normalize_memory

    memory = normalize_memory(load_user_memory())
    return {"verified_experiences": list_verified_experiences(memory)}


@app.get("/api/v1/memory/pending")
def get_pending_experiences() -> dict[str, Any]:
    from agents.memory_builder import list_pending_experiences, normalize_memory

    memory = normalize_memory(load_user_memory())
    return {"pending_experiences": list_pending_experiences(memory)}


@app.post("/api/v1/memory/experiences/propose")
async def propose_memory_experience(payload: ExperiencePropose) -> dict[str, Any]:
    from agents.memory_builder import MemoryBuilderAgent, MemoryBuilderInput

    agent = MemoryBuilderAgent()
    try:
        result = await agent.run(
            MemoryBuilderInput(
                action="propose",
                statement=payload.statement,
                category=payload.category,  # type: ignore[arg-type]
                tags=payload.tags,
                related_projects=payload.related_projects,
                persist=payload.persist,
                user_memory=load_user_memory(),
            )
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return {
        "changed": result.changed,
        "pending_experiences": result.pending,
        "verified_experiences": result.verified,
    }


@app.post("/api/v1/memory/experiences/approve")
async def approve_memory_experience(payload: ExperienceDecision) -> dict[str, Any]:
    from agents.memory_builder import MemoryBuilderAgent, MemoryBuilderInput

    agent = MemoryBuilderAgent()
    try:
        result = await agent.run(
            MemoryBuilderInput(
                action="approve",
                experience_id=payload.experience_id,
                persist=payload.persist,
                user_memory=load_user_memory(),
            )
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return {
        "changed": result.changed,
        "pending_experiences": result.pending,
        "verified_experiences": result.verified,
    }


@app.post("/api/v1/memory/experiences/reject")
async def reject_memory_experience(payload: ExperienceDecision) -> dict[str, Any]:
    from agents.memory_builder import MemoryBuilderAgent, MemoryBuilderInput

    agent = MemoryBuilderAgent()
    try:
        result = await agent.run(
            MemoryBuilderInput(
                action="reject",
                experience_id=payload.experience_id,
                persist=payload.persist,
                user_memory=load_user_memory(),
            )
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return {
        "changed": result.changed,
        "pending_experiences": result.pending,
        "verified_experiences": result.verified,
    }


@app.post("/api/v1/generate")
async def generate(payload: GenerateRequest, session: Session = Depends(get_session)) -> dict[str, Any]:
    modes = load_content_modes().get("modes", {})
    if payload.content_mode not in modes:
        raise HTTPException(status_code=400, detail=f"Unknown content_mode: {payload.content_mode}")

    provider = get_provider()
    result = await run_generation_pipeline(
        provider,
        topic=payload.topic,
        content_mode=payload.content_mode,
        format=payload.format,
        audience=payload.audience,
        fake=settings.use_fake_provider,
        selected_angle_index=payload.selected_angle_index,
    )

    if payload.save:
        user = _ensure_local_user(session)
        # Hard safety gate: unsupported personal claims cannot be approved.
        status = "unsafe" if not result.get("approval_allowed", True) else "draft"
        post = Post(
            user_id=user.id,
            topic=payload.topic,
            format=payload.format,
            content_mode=payload.content_mode,
            status=status,
            body=result["final_text"],
            critic_scores=result["critic"]["scores"],
            engagement_prediction=result["engagement_prediction"],
            tags=["grounding:unsafe"] if status == "unsafe" else [],
        )
        session.add(post)
        session.flush()
        pipeline_run_id = uuid.UUID(result["pipeline_run_id"])
        for stage_name, stage_payload in result["stages"].items():
            session.add(
                GeneratedContent(
                    user_id=user.id,
                    post_id=post.id,
                    pipeline_run_id=pipeline_run_id,
                    stage=stage_name,
                    format=payload.format,
                    prompt_context={"topic": payload.topic, "content_mode": payload.content_mode},
                    model_provider=stage_payload.get("meta", {}).get("provider", provider.name),
                    model_name=stage_payload.get("meta", {}).get("model", settings.default_model),
                    input_text=payload.topic if stage_name == "writer" else result.get("draft"),
                    output_text=stage_payload.get("text"),
                    output_json=stage_payload,
                )
            )
        session.add(
            Feedback(
                user_id=user.id,
                post_id=post.id,
                source="critic",
                scores=result["critic"]["scores"],
                issues=result["critic"]["issues"],
            )
        )
        session.add(
            Feedback(
                user_id=user.id,
                post_id=post.id,
                source="engagement_predictor",
                scores=result["engagement_prediction"],
                problems=result["engagement_prediction"].get("problems", []),
                improvements=result["engagement_prediction"].get("improvements", []),
            )
        )
        session.commit()
        result["post_id"] = str(post.id)

    return result


@app.get("/api/v1/posts")
def list_posts(session: Session = Depends(get_session)) -> list[dict[str, Any]]:
    posts = session.query(Post).order_by(Post.created_at.desc()).all()
    return [
        {
            "id": str(post.id),
            "topic": post.topic,
            "format": post.format,
            "content_mode": post.content_mode,
            "status": post.status,
            "body": post.body,
            "critic_scores": post.critic_scores,
            "engagement_prediction": post.engagement_prediction,
            "created_at": post.created_at.isoformat() if post.created_at else None,
        }
        for post in posts
    ]


@app.get("/api/v1/posts/{post_id}")
def get_post(post_id: uuid.UUID, session: Session = Depends(get_session)) -> dict[str, Any]:
    post = session.get(Post, post_id)
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    return {
        "id": str(post.id),
        "topic": post.topic,
        "format": post.format,
        "content_mode": post.content_mode,
        "status": post.status,
        "body": post.body,
        "critic_scores": post.critic_scores,
        "engagement_prediction": post.engagement_prediction,
        "tags": post.tags,
    }


@app.patch("/api/v1/posts/{post_id}")
def patch_post(
    post_id: uuid.UUID, payload: PostUpdate, session: Session = Depends(get_session)
) -> dict[str, Any]:
    from agents.grounding import check_claims
    from shared.knowledge import load_user_memory

    post = session.get(Post, post_id)
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    if payload.body is not None:
        post.body = payload.body
    if payload.status is not None:
        # Hard safety gate: cannot approve content with unsupported personal claims.
        if payload.status in {"ready", "reviewed"}:
            body = payload.body if payload.body is not None else post.body
            grounding = check_claims(body or "", load_user_memory())
            if not grounding.safe:
                raise HTTPException(
                    status_code=400,
                    detail={
                        "error": "approval_blocked",
                        "message": "Unsupported personal claims prevent final approval",
                        "rejected_claims": [c.model_dump() for c in grounding.rejected_claims],
                    },
                )
        post.status = payload.status
    if payload.title is not None:
        post.title = payload.title
    if payload.tags is not None:
        post.tags = payload.tags
    session.commit()
    return {"id": str(post.id), "status": post.status, "body": post.body}


@app.post("/api/v1/posts/{post_id}/evidence")
def add_evidence(
    post_id: uuid.UUID, payload: EvidenceCreate, session: Session = Depends(get_session)
) -> dict[str, Any]:
    post = session.get(Post, post_id)
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    user = _ensure_local_user(session)
    source = ResearchSource(
        user_id=user.id,
        source=payload.source,
        url=payload.url,
        title=payload.title,
        published_or_accessed_at=payload.date,
        confidence=payload.confidence,
        extracted_claim=payload.extracted_claim,
    )
    session.add(source)
    session.flush()
    session.add(
        PostSource(
            post_id=post.id,
            research_source_id=source.id,
            extracted_claim=payload.extracted_claim,
            confidence=payload.confidence,
        )
    )
    # Also write a local evidence file for the filesystem layer.
    evidence_dir = repo_path(settings.research_sources_dir)
    evidence_dir.mkdir(parents=True, exist_ok=True)
    evidence_path = evidence_dir / f"{source.id}.json"
    evidence_path.write_text(
        json.dumps(
            {
                "id": str(source.id),
                "source": payload.source,
                "date": payload.date,
                "confidence": payload.confidence,
                "extracted_claim": payload.extracted_claim,
                "post_id": str(post.id),
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    session.commit()
    return {"id": str(source.id), "post_id": str(post.id)}


@app.get("/api/v1/posts/{post_id}/evidence")
def list_evidence(post_id: uuid.UUID, session: Session = Depends(get_session)) -> list[dict[str, Any]]:
    links = session.query(PostSource).filter(PostSource.post_id == post_id).all()
    results: list[dict[str, Any]] = []
    for link in links:
        source = session.get(ResearchSource, link.research_source_id)
        if not source:
            continue
        results.append(
            {
                "id": str(source.id),
                "source": source.source,
                "date": source.published_or_accessed_at,
                "confidence": float(source.confidence) if source.confidence is not None else None,
                "extracted_claim": source.extracted_claim or link.extracted_claim,
            }
        )
    return results


@app.post("/api/v1/posts/{post_id}/engagement-feedback")
def add_engagement_feedback(
    post_id: uuid.UUID, payload: EngagementFeedbackCreate, session: Session = Depends(get_session)
) -> dict[str, Any]:
    post = session.get(Post, post_id)
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    user = _ensure_local_user(session)
    row = EngagementFeedback(
        user_id=user.id,
        post_id=post.id,
        impressions=payload.impressions,
        likes=payload.likes,
        comments=payload.comments,
        reposts=payload.reposts,
        saves=payload.saves,
        user_rating=payload.user_rating,
        content_mode=post.content_mode,
        topic=post.topic,
        notes=payload.notes,
    )
    session.add(row)
    session.commit()

    feedback_path = repo_path(settings.engagement_feedback_path)
    if feedback_path.exists():
        data = json.loads(feedback_path.read_text(encoding="utf-8"))
    else:
        data = {"entries": []}
    data.setdefault("entries", []).append(
        {
            "post_id": str(post.id),
            "recorded_at": row.recorded_at.isoformat(),
            "impressions": payload.impressions,
            "likes": payload.likes,
            "comments": payload.comments,
            "reposts": payload.reposts,
            "saves": payload.saves,
            "user_rating": payload.user_rating,
            "notes": payload.notes,
            "content_mode": post.content_mode,
            "topic": post.topic,
        }
    )
    feedback_path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    return {"id": str(row.id), "post_id": str(post.id)}


@app.get("/api/v1/posts/{post_id}/engagement-feedback")
def get_engagement_feedback(
    post_id: uuid.UUID, session: Session = Depends(get_session)
) -> list[dict[str, Any]]:
    rows = (
        session.query(EngagementFeedback)
        .filter(EngagementFeedback.post_id == post_id)
        .order_by(EngagementFeedback.recorded_at.desc())
        .all()
    )
    return [
        {
            "id": str(row.id),
            "impressions": row.impressions,
            "likes": row.likes,
            "comments": row.comments,
            "reposts": row.reposts,
            "saves": row.saves,
            "user_rating": row.user_rating,
            "recorded_at": row.recorded_at.isoformat() if row.recorded_at else None,
        }
        for row in rows
    ]
