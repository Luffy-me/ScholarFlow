"""Initial Phase 1 schema.

Revision ID: 0001_phase1
Revises:
Create Date: 2026-07-19
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "0001_phase1"
down_revision = None
branch_labels = None
depends_on = None


def _json_type():
    return sa.JSON().with_variant(postgresql.JSONB(), "postgresql")


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("email", sa.Text(), nullable=True, unique=True),
        sa.Column("display_name", sa.Text(), nullable=False),
        sa.Column("timezone", sa.Text(), nullable=False),
        sa.Column("preferences", _json_type(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_table(
        "writing_profiles",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("user_id", sa.Uuid(), sa.ForeignKey("users.id"), nullable=False, unique=True),
        sa.Column("tone", sa.Text(), nullable=True),
        sa.Column("voice_traits", _json_type(), nullable=False),
        sa.Column("preferred_formats", _json_type(), nullable=False),
        sa.Column("allowed_experiences", _json_type(), nullable=False),
        sa.Column("background", _json_type(), nullable=False),
        sa.Column("skills", _json_type(), nullable=False),
        sa.Column("projects", _json_type(), nullable=False),
        sa.Column("preferred_topics", _json_type(), nullable=False),
        sa.Column("vocabulary_preferences", _json_type(), nullable=False),
        sa.Column("content_preferences", _json_type(), nullable=False),
        sa.Column("style", _json_type(), nullable=False),
        sa.Column("memory_snapshot", _json_type(), nullable=False),
        sa.Column("banned_topics", _json_type(), nullable=False),
        sa.Column("style_rules_override", _json_type(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_table(
        "posts",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("user_id", sa.Uuid(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("topic", sa.Text(), nullable=False),
        sa.Column("format", sa.Text(), nullable=False),
        sa.Column("content_mode", sa.Text(), nullable=False),
        sa.Column("status", sa.Text(), nullable=False),
        sa.Column("title", sa.Text(), nullable=True),
        sa.Column("body", sa.Text(), nullable=False),
        sa.Column("hook", sa.Text(), nullable=True),
        sa.Column("discussion_question", sa.Text(), nullable=True),
        sa.Column("strategy", _json_type(), nullable=True),
        sa.Column("critic_scores", _json_type(), nullable=True),
        sa.Column("engagement_prediction", _json_type(), nullable=True),
        sa.Column("tags", _json_type(), nullable=False),
        sa.Column("published_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_table(
        "generated_content",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("user_id", sa.Uuid(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("post_id", sa.Uuid(), sa.ForeignKey("posts.id"), nullable=True),
        sa.Column("pipeline_run_id", sa.Uuid(), nullable=False),
        sa.Column("stage", sa.Text(), nullable=False),
        sa.Column("format", sa.Text(), nullable=False),
        sa.Column("prompt_context", _json_type(), nullable=False),
        sa.Column("model_provider", sa.Text(), nullable=False),
        sa.Column("model_name", sa.Text(), nullable=False),
        sa.Column("input_text", sa.Text(), nullable=True),
        sa.Column("output_text", sa.Text(), nullable=True),
        sa.Column("output_json", _json_type(), nullable=True),
        sa.Column("latency_ms", sa.Integer(), nullable=True),
        sa.Column("token_usage", _json_type(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_table(
        "research_sources",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("user_id", sa.Uuid(), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("source", sa.Text(), nullable=False),
        sa.Column("url", sa.Text(), nullable=True),
        sa.Column("title", sa.Text(), nullable=True),
        sa.Column("source_type", sa.Text(), nullable=False),
        sa.Column("publisher", sa.Text(), nullable=True),
        sa.Column("published_or_accessed_at", sa.Text(), nullable=True),
        sa.Column("confidence", sa.Numeric(4, 3), nullable=True),
        sa.Column("extracted_claim", sa.Text(), nullable=True),
        sa.Column("summary", sa.Text(), nullable=True),
        sa.Column("raw_excerpt", sa.Text(), nullable=True),
        sa.Column("metadata", _json_type(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_table(
        "post_sources",
        sa.Column("post_id", sa.Uuid(), sa.ForeignKey("posts.id"), primary_key=True),
        sa.Column("research_source_id", sa.Uuid(), sa.ForeignKey("research_sources.id"), primary_key=True),
        sa.Column("relevance_note", sa.Text(), nullable=True),
        sa.Column("extracted_claim", sa.Text(), nullable=True),
        sa.Column("confidence", sa.Numeric(4, 3), nullable=True),
    )
    op.create_table(
        "feedback",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("user_id", sa.Uuid(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("post_id", sa.Uuid(), sa.ForeignKey("posts.id"), nullable=True),
        sa.Column("generated_content_id", sa.Uuid(), sa.ForeignKey("generated_content.id"), nullable=True),
        sa.Column("source", sa.Text(), nullable=False),
        sa.Column("rating", sa.Integer(), nullable=True),
        sa.Column("scores", _json_type(), nullable=True),
        sa.Column("problems", _json_type(), nullable=False),
        sa.Column("improvements", _json_type(), nullable=False),
        sa.Column("issues", _json_type(), nullable=False),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_table(
        "engagement_feedback",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("user_id", sa.Uuid(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("post_id", sa.Uuid(), sa.ForeignKey("posts.id"), nullable=False),
        sa.Column("recorded_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("impressions", sa.Integer(), nullable=False),
        sa.Column("likes", sa.Integer(), nullable=False),
        sa.Column("comments", sa.Integer(), nullable=False),
        sa.Column("reposts", sa.Integer(), nullable=False),
        sa.Column("saves", sa.Integer(), nullable=False),
        sa.Column("user_rating", sa.Integer(), nullable=True),
        sa.Column("content_mode", sa.Text(), nullable=True),
        sa.Column("topic", sa.Text(), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("raw_payload", _json_type(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("engagement_feedback")
    op.drop_table("feedback")
    op.drop_table("post_sources")
    op.drop_table("research_sources")
    op.drop_table("generated_content")
    op.drop_table("posts")
    op.drop_table("writing_profiles")
    op.drop_table("users")
