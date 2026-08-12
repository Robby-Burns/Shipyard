"""add model catalog snapshots and routing outcomes

Revision ID: 8f1d9d4b2c11
Revises: 576b184229c1
Create Date: 2026-08-12
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "8f1d9d4b2c11"
down_revision: Union[str, Sequence[str], None] = "576b184229c1"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "model_catalog_snapshots",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("provider", sa.String(length=50), nullable=False),
        sa.Column("model_id", sa.String(length=255), nullable=False),
        sa.Column("model_name", sa.String(length=255), nullable=True),
        sa.Column("context_length", sa.Integer(), nullable=True),
        sa.Column("max_completion_tokens", sa.Integer(), nullable=True),
        sa.Column("input_price_per_million", sa.Float(), nullable=True),
        sa.Column("output_price_per_million", sa.Float(), nullable=True),
        sa.Column("supported_parameters", sa.JSON(), nullable=True),
        sa.Column("benchmarks", sa.JSON(), nullable=True),
        sa.Column("raw_metadata", sa.JSON(), nullable=True),
        sa.Column("is_available", sa.Boolean(), nullable=False),
        sa.Column("fetched_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_model_catalog_snapshots_provider", "model_catalog_snapshots", ["provider"])
    op.create_index("ix_model_catalog_snapshots_model_id", "model_catalog_snapshots", ["model_id"])
    op.create_table(
        "model_routing_outcomes",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("request_id", sa.String(length=100), nullable=True),
        sa.Column("capability", sa.String(length=100), nullable=False),
        sa.Column("model_id", sa.String(length=255), nullable=False),
        sa.Column("prompt_tokens", sa.Integer(), nullable=True),
        sa.Column("completion_tokens", sa.Integer(), nullable=True),
        sa.Column("estimated_cost", sa.Float(), nullable=True),
        sa.Column("latency_ms", sa.Float(), nullable=True),
        sa.Column("success", sa.Boolean(), nullable=False),
        sa.Column("quality_score", sa.Float(), nullable=True),
        sa.Column("finish_reason", sa.String(length=50), nullable=True),
        sa.Column("error_code", sa.String(length=100), nullable=True),
        sa.Column("error_message", sa.String(length=500), nullable=True),
        sa.Column("task_features", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_model_routing_outcomes_request_id", "model_routing_outcomes", ["request_id"])
    op.create_index("ix_model_routing_outcomes_capability", "model_routing_outcomes", ["capability"])
    op.create_index("ix_model_routing_outcomes_model_id", "model_routing_outcomes", ["model_id"])
    op.create_index("ix_model_routing_outcomes_created_at", "model_routing_outcomes", ["created_at"])


def downgrade() -> None:
    op.drop_index("ix_model_routing_outcomes_created_at", table_name="model_routing_outcomes")
    op.drop_index("ix_model_routing_outcomes_model_id", table_name="model_routing_outcomes")
    op.drop_index("ix_model_routing_outcomes_capability", table_name="model_routing_outcomes")
    op.drop_index("ix_model_routing_outcomes_request_id", table_name="model_routing_outcomes")
    op.drop_table("model_routing_outcomes")
    op.drop_index("ix_model_catalog_snapshots_model_id", table_name="model_catalog_snapshots")
    op.drop_index("ix_model_catalog_snapshots_provider", table_name="model_catalog_snapshots")
    op.drop_table("model_catalog_snapshots")
