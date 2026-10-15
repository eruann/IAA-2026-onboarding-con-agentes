"""Crea las tablas del juego

Revision ID: 0003
Revises: 0002
Create Date: 2026-10-10
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0003"
down_revision: str | None = "0002"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "people",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("slack_user_id", sa.String(length=64), nullable=True),
        sa.Column("name", sa.String(length=160), nullable=False),
        sa.Column("role", sa.String(length=160), nullable=False),
        sa.Column("area", sa.String(length=120), nullable=False),
        sa.Column("is_newcomer", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.UniqueConstraint("slack_user_id"),
    )
    op.create_table(
        "quests",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("key", sa.String(length=80), nullable=False, unique=True),
        sa.Column("title", sa.String(length=200), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("points", sa.Integer(), nullable=False),
        sa.Column("approver", sa.String(length=32), nullable=False),
        sa.Column("evidence_required", sa.Text(), nullable=False),
    )
    op.create_table(
        "quest_assignments",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("quest_id", sa.Integer(), sa.ForeignKey("quests.id"), nullable=False),
        sa.Column("person_id", sa.Integer(), sa.ForeignKey("people.id"), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False, server_default="pending"),
        sa.Column("assigned_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_table(
        "evidence",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "assignment_id",
            sa.Integer(),
            sa.ForeignKey("quest_assignments.id"),
            nullable=False,
        ),
        sa.Column("text", sa.Text(), nullable=True),
        sa.Column("url", sa.String(length=2048), nullable=True),
        sa.Column("submitted_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_table(
        "approvals",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "assignment_id",
            sa.Integer(),
            sa.ForeignKey("quest_assignments.id"),
            nullable=False,
        ),
        sa.Column("approved_by", sa.Integer(), sa.ForeignKey("people.id"), nullable=True),
        sa.Column("approver_type", sa.String(length=32), nullable=False),
        sa.Column("decision", sa.String(length=32), nullable=False),
        sa.Column("decided_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint(
            "approver_type IN ('manager', 'helpdesk', 'agent')",
            name="ck_approvals_approver_type",
        ),
        sa.CheckConstraint(
            "(approver_type = 'agent' AND approved_by IS NULL) "
            "OR (approver_type != 'agent' AND approved_by IS NOT NULL)",
            name="ck_approvals_approver_person",
        ),
    )
    op.create_table(
        "redemptions",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("person_id", sa.Integer(), sa.ForeignKey("people.id"), nullable=False),
        sa.Column("reward_key", sa.String(length=80), nullable=False),
        sa.Column("points_spent", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("redemptions")
    op.drop_table("approvals")
    op.drop_table("evidence")
    op.drop_table("quest_assignments")
    op.drop_table("quests")
    op.drop_table("people")
