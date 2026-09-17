"""Modelo de dominio de las misiones."""

from dataclasses import dataclass
from typing import Literal

QuestStatus = Literal["pending", "submitted", "approved", "rejected"]
Approver = Literal["manager", "helpdesk", "agent"]


@dataclass(frozen=True)
class Quest:
    key: str
    title: str
    description: str
    points: int
    approver: Approver
    evidence_required: str


# TODO(experiencia): las 6-8 misiones del TP salen de data/quests.yaml, no
# hardcodeadas acá. Este dataclass es solo la forma que tienen.
