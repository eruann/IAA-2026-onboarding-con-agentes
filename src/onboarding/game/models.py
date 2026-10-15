# recorrido: tablas-juego
"""Tablas del juego. Titular: rol Experiencia.

`approvals` registra quién aprobó y cuándo para poder medir las horas-persona
de la organización.
"""

from datetime import UTC, datetime

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column

from onboarding.db.base import Base


class Person(Base):
    __tablename__ = "people"

    id: Mapped[int] = mapped_column(primary_key=True)
    slack_user_id: Mapped[str | None] = mapped_column(String(64), unique=True)
    name: Mapped[str] = mapped_column(String(160), nullable=False)
    role: Mapped[str] = mapped_column(String(160), nullable=False)
    area: Mapped[str] = mapped_column(String(120), nullable=False)
    is_newcomer: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)


class QuestRow(Base):
    __tablename__ = "quests"
    __table_args__ = (
        CheckConstraint(
            "approver IN ('manager', 'helpdesk', 'agent')",
            name="ck_quests_approver",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    key: Mapped[str] = mapped_column(String(80), unique=True, nullable=False)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    points: Mapped[int] = mapped_column(Integer, nullable=False)
    approver: Mapped[str] = mapped_column(String(32), nullable=False)
    evidence_required: Mapped[str] = mapped_column(Text, nullable=False)


class QuestAssignment(Base):
    __tablename__ = "quest_assignments"
    __table_args__ = (
        UniqueConstraint(
            "quest_id", "person_id", name="uq_quest_assignments_quest_person"
        ),
        CheckConstraint(
            "status IN ('pending', 'submitted', 'approved', 'rejected')",
            name="ck_quest_assignments_status",
        ),
        Index("ix_quest_assignments_person_status", "person_id", "status"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    quest_id: Mapped[int] = mapped_column(ForeignKey("quests.id"), nullable=False)
    person_id: Mapped[int] = mapped_column(ForeignKey("people.id"), nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="pending")
    assigned_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(UTC),
        server_default=func.now(),
    )
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class Evidence(Base):
    __tablename__ = "evidence"
    __table_args__ = (
        CheckConstraint(
            "text IS NOT NULL OR url IS NOT NULL",
            name="ck_evidence_has_content",
        ),
        Index("ix_evidence_assignment_id", "assignment_id"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    assignment_id: Mapped[int] = mapped_column(
        ForeignKey("quest_assignments.id"), nullable=False
    )
    text: Mapped[str | None] = mapped_column(Text)
    url: Mapped[str | None] = mapped_column(String(2048))
    submitted_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(UTC),
        server_default=func.now(),
    )


class Approval(Base):
    __tablename__ = "approvals"
    __table_args__ = (
        CheckConstraint(
            "approver_type IN ('manager', 'helpdesk', 'agent')",
            name="ck_approvals_approver_type",
        ),
        CheckConstraint(
            "(approver_type = 'agent' AND approved_by IS NULL) "
            "OR (approver_type != 'agent' AND approved_by IS NOT NULL)",
            name="ck_approvals_approver_person",
        ),
        CheckConstraint(
            "decision IN ('approved', 'rejected')",
            name="ck_approvals_decision",
        ),
        Index("ix_approvals_assignment_id", "assignment_id"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    assignment_id: Mapped[int] = mapped_column(
        ForeignKey("quest_assignments.id"), nullable=False
    )
    approved_by: Mapped[int | None] = mapped_column(ForeignKey("people.id"))
    approver_type: Mapped[str] = mapped_column(String(32), nullable=False)
    decision: Mapped[str] = mapped_column(String(32), nullable=False)
    decided_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(UTC),
        server_default=func.now(),
    )


class Redemption(Base):
    __tablename__ = "redemptions"
    __table_args__ = (Index("ix_redemptions_person_id", "person_id"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    person_id: Mapped[int] = mapped_column(ForeignKey("people.id"), nullable=False)
    reward_key: Mapped[str] = mapped_column(String(80), nullable=False)
    points_spent: Mapped[int] = mapped_column(Integer, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(UTC),
        server_default=func.now(),
    )
