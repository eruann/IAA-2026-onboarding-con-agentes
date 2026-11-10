from pathlib import Path

import pytest
import yaml
from sqlalchemy import select
from sqlalchemy.orm import Session

from onboarding.game.board import employee_board, manager_board
from onboarding.game.models import Person, QuestAssignment, QuestRow, Redemption


def _use_people_yaml(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, people: list[dict]) -> None:
    (tmp_path / "people.yaml").write_text(
        yaml.safe_dump(people, allow_unicode=True), encoding="utf-8"
    )
    monkeypatch.setattr("onboarding.paths.DATA_DIR", tmp_path)


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
def test_el_tablero_filtra_ingresantes_y_misiones_por_jefe(
    db_session: Session,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    people_data = [
        {
            "key": "t-manager-a",
            "name": "Jefa A",
            "role": "Jefa",
            "area": "X",
            "is_newcomer": False,
            "is_manager": True,
        },
        {
            "key": "t-manager-b",
            "name": "Jefe B",
            "role": "Jefe",
            "area": "X",
            "is_newcomer": False,
            "is_manager": True,
        },
        {
            "key": "t-new-a1",
            "name": "Ingresante A1",
            "role": "Analista",
            "area": "X",
            "is_newcomer": True,
            "manager_key": "t-manager-a",
        },
        {
            "key": "t-new-a2",
            "name": "Ingresante A2",
            "role": "Analista",
            "area": "X",
            "is_newcomer": True,
            "manager_key": "t-manager-a",
        },
        {
            "key": "t-new-b1",
            "name": "Ingresante B1",
            "role": "Analista",
            "area": "X",
            "is_newcomer": True,
            "manager_key": "t-manager-b",
        },
        {
            "key": "t-new-unmanaged",
            "name": "Ingresante sin equipo",
            "role": "Analista",
            "area": "X",
            "is_newcomer": True,
        },
    ]
    _use_people_yaml(tmp_path, monkeypatch, people_data)
    people = [
        Person(
            key=item["key"],
            name=item["name"],
            role=item["role"],
            area=item["area"],
            is_newcomer=item["is_newcomer"],
        )
        for item in people_data
    ]
    quests = [_quest("t-team-mission-a", 10), _quest("t-team-mission-b", 20)]
    db_session.add_all([*people, *quests])
    db_session.flush()
    people_by_key = {person.key: person for person in people}
    db_session.add_all(
        [
            QuestAssignment(
                person_id=people_by_key[person_key].id,
                quest_id=quests[index % len(quests)].id,
                status="submitted",
            )
            for index, person_key in enumerate(("t-new-a1", "t-new-a2", "t-new-b1"))
        ]
    )
    db_session.flush()

    board_a = manager_board(db_session, manager_key="t-manager-a")
    board_b = manager_board(db_session, manager_key="t-manager-b")
    board_invalid = manager_board(db_session, manager_key="t-new-unmanaged")

    assert {person.key for person in board_a.newcomers} == {"t-new-a1", "t-new-a2"}
    assert [item.person for item in board_a.pending] == ["Ingresante A1", "Ingresante A2"]
    assert {person.key for person in board_b.newcomers} == {"t-new-b1"}
    assert [item.person for item in board_b.pending] == ["Ingresante B1"]
    assert board_invalid.newcomers == [] and board_invalid.pending == []


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
