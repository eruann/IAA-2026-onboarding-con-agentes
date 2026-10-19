"""Tabla de chunks (ADR 0005: embeddings bge-m3, dimensión 1024)

Revision ID: 0003
Revises: 0002
Create Date: 2026-10-19
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from pgvector.sqlalchemy import Vector

revision: str = "0003"
down_revision: str | None = "0002"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

EMBEDDING_DIMENSION = 1024


def upgrade() -> None:
    op.create_table(
        "chunks",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("document", sa.String(length=255), nullable=False),
        sa.Column("section", sa.String(length=255), nullable=True),
        sa.Column("text", sa.Text(), nullable=False),
        sa.Column("embedding", Vector(EMBEDDING_DIMENSION), nullable=False),
    )
    op.create_index("ix_chunks_document", "chunks", ["document"])


def downgrade() -> None:
    op.drop_index("ix_chunks_document", table_name="chunks")
    op.drop_table("chunks")
