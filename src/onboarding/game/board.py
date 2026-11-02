# producto
# Este archivo es parte del producto: el asistente de onboarding que se
# entrega y se evalúa.

"""El tablero del ingresante: sus misiones, sus puntos y su nivel.

Solo lee. Entregar evidencia, aprobar y canjear se hacen en otro lado.
"""

from dataclasses import dataclass

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from onboarding.db.session import get_engine
from onboarding.game.models import Person, QuestAssignment, QuestRow, Redemption
from onboarding.game.points import level_for
from onboarding.game.quests import QuestStatus

# Primero lo que espera algo de la persona o de su jefe; al final, lo ya cerrado
STATUS_ORDER: dict[str, int] = {"rejected": 0, "pending": 1, "submitted": 2, "approved": 3}


@dataclass(frozen=True)
class MissionCard:
    key: str
    title: str
    description: str
    points: int
    status: QuestStatus
    evidence_required: str


@dataclass(frozen=True)
class EmployeeBoard:
    missions: list[MissionCard]
    earned: int  # puntos de las misiones aprobadas
    spent: int  # puntos ya canjeados

    @property
    def available(self) -> int:
        return self.earned - self.spent

    @property
    def level(self) -> str:
        return level_for(self.earned)


# recorrido: tablero-empleado
def employee_board(person_key: str, session: Session | None = None) -> EmployeeBoard:
    """El tablero de una persona. Si no existe o no tiene misiones, queda vacío."""
    if session is None:
        with Session(get_engine()) as own_session:
            return _board(own_session, person_key)
    return _board(session, person_key)


def _board(session: Session, person_key: str) -> EmployeeBoard:
    person_id = session.scalar(select(Person.id).where(Person.key == person_key))
    if person_id is None:
        return EmployeeBoard(missions=[], earned=0, spent=0)
    rows = session.execute(
        select(QuestRow, QuestAssignment.status)
        .join(QuestAssignment, QuestAssignment.quest_id == QuestRow.id)
        .where(QuestAssignment.person_id == person_id)
    ).all()
    missions = sorted(
        (
            MissionCard(
                quest.key,
                quest.title,
                quest.description,
                quest.points,
                status,
                quest.evidence_required,
            )
            for quest, status in rows
        ),
        key=lambda mission: (STATUS_ORDER.get(mission.status, 9), mission.title),
    )
    spent = session.scalar(
        select(func.coalesce(func.sum(Redemption.points_spent), 0)).where(
            Redemption.person_id == person_id
        )
    )
    earned = sum(mission.points for mission in missions if mission.status == "approved")
    return EmployeeBoard(missions=missions, earned=earned, spent=spent)
