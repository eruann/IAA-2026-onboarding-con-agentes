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
        sa.CheckConstraint(
            "approver IN ('manager', 'helpdesk', 'agent')",
            name="ck_quests_approver",
        ),
    )
    op.create_table(
        "quest_assignments",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("quest_id", sa.Integer(), sa.ForeignKey("quests.id"), nullable=False),
        sa.Column("person_id", sa.Integer(), sa.ForeignKey("people.id"), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False, server_default="pending"),
        sa.Column(
            "assigned_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.UniqueConstraint(
            "quest_id", "person_id", name="uq_quest_assignments_quest_person"
        ),
        sa.CheckConstraint(
            "status IN ('pending', 'submitted', 'approved', 'rejected')",
            name="ck_quest_assignments_status",
        ),
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
        sa.Column(
            "submitted_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.CheckConstraint(
            "text IS NOT NULL OR url IS NOT NULL",
            name="ck_evidence_has_content",
        ),
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
        sa.Column(
            "decided_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.CheckConstraint(
            "approver_type IN ('manager', 'helpdesk', 'agent')",
            name="ck_approvals_approver_type",
        ),
        sa.CheckConstraint(
            "(approver_type = 'agent' AND approved_by IS NULL) "
            "OR (approver_type != 'agent' AND approved_by IS NOT NULL)",
            name="ck_approvals_approver_person",
        ),
        sa.CheckConstraint(
            "decision IN ('approved', 'rejected')",
            name="ck_approvals_decision",
        ),
    )
    op.create_table(
        "redemptions",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("person_id", sa.Integer(), sa.ForeignKey("people.id"), nullable=False),
        sa.Column("reward_key", sa.String(length=80), nullable=False),
        sa.Column("points_spent", sa.Integer(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
    )
    op.create_index(
        "ix_quest_assignments_person_status",
        "quest_assignments",
        ["person_id", "status"],
    )
    op.create_index("ix_evidence_assignment_id", "evidence", ["assignment_id"])
    op.create_index("ix_approvals_assignment_id", "approvals", ["assignment_id"])
    op.create_index("ix_redemptions_person_id", "redemptions", ["person_id"])


def downgrade() -> None:
    op.drop_index("ix_redemptions_person_id", table_name="redemptions")
    op.drop_index("ix_approvals_assignment_id", table_name="approvals")
    op.drop_index("ix_evidence_assignment_id", table_name="evidence")
    op.drop_index("ix_quest_assignments_person_status", table_name="quest_assignments")
    op.drop_table("redemptions")
    op.drop_table("approvals")
    op.drop_table("evidence")
    op.drop_table("quest_assignments")
    op.drop_table("quests")
    op.drop_table("people")
