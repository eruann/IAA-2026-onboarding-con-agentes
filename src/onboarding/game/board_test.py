import pytest
from sqlalchemy import select
from sqlalchemy.orm import Session

from onboarding.game.board import employee_board, manager_board
from onboarding.game.models import Person, QuestAssignment, QuestRow, Redemption


def _quest(key: str, points: int) -> QuestRow:
    return QuestRow(
        key=key,
        title=f"Misión {key}",
        description="Algo",
        points=points,
        approver="manager",
        evidence_required="Una prueba",
    )


@pytest.mark.db
def test_el_tablero_suma_las_aprobadas_y_descuenta_lo_canjeado(db_session: Session) -> None:
    person = Person(key="t-ana", name="Ana", role="Analista", area="X", is_newcomer=True)
    quests = [_quest("t-a", 60), _quest("t-b", 50), _quest("t-c", 30)]
    db_session.add_all([person, *quests])
    db_session.flush()
    for quest, status in zip(quests, ("approved", "approved", "pending"), strict=True):
        db_session.add(QuestAssignment(person_id=person.id, quest_id=quest.id, status=status))
    db_session.add(Redemption(person_id=person.id, reward_key="cafe", points_spent=50))
    db_session.flush()

    board = employee_board("t-ana", db_session)

    assert (board.earned, board.spent, board.available) == (110, 50, 60)
    assert board.level == "En marcha"
    # Lo pendiente primero, lo aprobado al final
    assert [mission.status for mission in board.missions] == ["pending", "approved", "approved"]


@pytest.mark.db
def test_una_persona_sin_misiones_tiene_el_tablero_vacio(db_session: Session) -> None:
    board = employee_board("no-existe", db_session)

    assert (board.missions, board.earned, board.available, board.level) == (
        [],
        0,
        0,
        "Recién llegado",
    )


@pytest.mark.db
def test_el_tablero_del_jefe_muestra_lo_que_espera_algo_y_ordena_como_la_base(
    db_session: Session,
) -> None:
    # Con acentos y minúsculas: el orden tiene que ser el de Postgres, no el de Python
    people = [
        Person(key=f"t-{name}", name=name, role="Analista", area="X", is_newcomer=True)
        for name in ("Ángela", "ana")
    ]
    quests = [_quest("t-m1", 10), _quest("t-m2", 20), _quest("t-m3", 30)]
    db_session.add_all([*people, *quests])
    db_session.flush()
    for person in people:
        for quest, status in zip(quests, ("pending", "submitted", "approved"), strict=True):
            db_session.add(QuestAssignment(person_id=person.id, quest_id=quest.id, status=status))
    db_session.flush()

    pending = [
        item for item in manager_board(db_session).pending if item.person in ("ana", "Ángela")
    ]

    # Primero lo entregado (lo que mueve el jefe), lo aprobado no aparece
    assert [item.status for item in pending] == ["submitted", "submitted", "pending", "pending"]
    # Dentro de cada estado, por nombre en el orden de la base (con su collation)
    by_db = db_session.scalars(
        select(Person.name).where(Person.key.in_(["t-Ángela", "t-ana"])).order_by(Person.name)
    ).all()
    assert [item.person for item in pending[:2]] == list(by_db)
    assert all(item.quest != "Misión t-m3" for item in pending)
