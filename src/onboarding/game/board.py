# producto
# Este archivo es parte del producto: el asistente de onboarding que se
# entrega y se evalúa.

"""Los tableros: el del ingresante (sus misiones, puntos y nivel) y el del jefe
(las misiones que esperan algo de los ingresantes).

Solo leen. Entregar evidencia, aprobar y canjear se hacen en otro lado.
"""

from dataclasses import dataclass

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from onboarding.db.session import session_scope
from onboarding.game.models import Person, QuestAssignment, QuestRow, Redemption
from onboarding.game.people import PersonCard, person_card
from onboarding.game.points import level_for
from onboarding.game.quests import QuestStatus

# Para el ingresante: primero lo que espera algo de él, al final lo ya cerrado
EMPLOYEE_ORDER: dict[str, int] = {"rejected": 0, "pending": 1, "submitted": 2, "approved": 3}
# Para el jefe: primero lo que tiene que mover él (evidencia entregada). Lo aprobado
# o rechazado ya no necesita nada de su parte y no se muestra.
MANAGER_ORDER: dict[str, int] = {"submitted": 0, "pending": 1}


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
    with session_scope(session) as db_session:
        return _board(db_session, person_key)


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
        key=lambda mission: (EMPLOYEE_ORDER.get(mission.status, 9), mission.title),
    )
    spent = session.scalar(
        select(func.coalesce(func.sum(Redemption.points_spent), 0)).where(
            Redemption.person_id == person_id
        )
    )
    earned = sum(mission.points for mission in missions if mission.status == "approved")
    return EmployeeBoard(missions=missions, earned=earned, spent=spent)


@dataclass(frozen=True)
class PendingMission:
    person: str
    quest: str
    status: QuestStatus


@dataclass(frozen=True)
class ManagerBoard:
    pending: list[PendingMission]
    newcomers: list[PersonCard]


# TODO(experiencia): solo el equipo de este jefe (falta saber quién es jefe de quién).
def manager_board(session: Session | None = None) -> ManagerBoard:
    """Las misiones de los ingresantes que esperan algo, y los ingresantes."""
    with session_scope(session) as db_session:
        newcomers = [
            person_card(person)
            for person in db_session.scalars(
                select(Person).where(Person.is_newcomer.is_(True)).order_by(Person.name)
            ).all()
        ]
        rows = db_session.execute(
            select(Person.name, QuestRow.title, QuestAssignment.status)
            .join(Person, QuestAssignment.person_id == Person.id)
            .join(QuestRow, QuestAssignment.quest_id == QuestRow.id)
            .where(Person.is_newcomer.is_(True), QuestAssignment.status.in_(MANAGER_ORDER))
        ).all()
    pending = sorted(
        (PendingMission(name, title, status) for name, title, status in rows),
        key=lambda item: (MANAGER_ORDER[item.status], item.person, item.quest),
    )
    return ManagerBoard(pending=pending, newcomers=newcomers)
