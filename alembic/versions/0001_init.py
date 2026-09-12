"""init hotelops tables

Revision ID: 0001_init
Revises:
Create Date: 2026-09-12
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0001_init"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "documents",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("doc_type", sa.String(64), nullable=False),
        sa.Column("surface", sa.String(16), nullable=False),
        sa.Column("market", sa.String(16), nullable=False),
        sa.Column("body", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_table(
        "action_runs",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("action_id", sa.String(128), nullable=False),
        sa.Column("actor", sa.String(64), nullable=False),
        sa.Column("role", sa.String(32), nullable=False),
        sa.Column("status", sa.String(32), nullable=False),
        sa.Column("input_json", sa.Text(), nullable=False),
        sa.Column("output_json", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_table(
        "audit_events",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("actor", sa.String(64), nullable=False),
        sa.Column("role", sa.String(32), nullable=False),
        sa.Column("method", sa.String(16), nullable=False),
        sa.Column("path", sa.String(255), nullable=False),
        sa.Column("status_code", sa.Integer(), nullable=False),
        sa.Column("detail", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_table(
        "stored_events",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("event_id", sa.String(32), nullable=False),
        sa.Column("topic", sa.String(128), nullable=False),
        sa.Column("surface", sa.String(16), nullable=False),
        sa.Column("source", sa.String(64), nullable=False),
        sa.Column("payload_json", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_table(
        "embedding_chunks",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("document_id", sa.Integer(), nullable=False),
        sa.Column("chunk", sa.Text(), nullable=False),
        sa.Column("token_count", sa.Integer(), nullable=False),
        sa.Column("lexical_norm", sa.Float(), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("embedding_chunks")
    op.drop_table("stored_events")
    op.drop_table("audit_events")
    op.drop_table("action_runs")
    op.drop_table("documents")
