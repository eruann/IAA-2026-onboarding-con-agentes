import pytest
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from onboarding.game.data import sync_game_data
from onboarding.game.models import Person, QuestAssignment, QuestRow

PEOPLE = [
    {
        "key": "data-test-nuevo",
        "name": "Nuevo",
        "role": "Analista",
        "area": "X",
        "is_newcomer": True,
    }
]
QUESTS = [
    {
        "key": "data-test-mision",
        "title": "Misión",
        "description": "Algo",
        "points": 10,
        "approver": "manager",
        "evidence_required": "Una prueba",
    }
]


@pytest.mark.db
def test_carga_personas_y_misiones_y_asigna_sin_duplicar(db_session: Session) -> None:
    sync_game_data(db_session, PEOPLE, QUESTS)
    sync_game_data(db_session, PEOPLE, QUESTS)

    person = db_session.scalar(select(Person).where(Person.key == "data-test-nuevo"))
    quest = db_session.scalar(select(QuestRow).where(QuestRow.key == "data-test-mision"))
    assignments = db_session.scalar(
        select(func.count(QuestAssignment.id)).where(
            QuestAssignment.person_id == person.id, QuestAssignment.quest_id == quest.id
        )
    )
    assert assignments == 1


@pytest.mark.db
def test_si_cambian_los_datos_actualiza_la_persona_y_la_mision(db_session: Session) -> None:
    sync_game_data(db_session, PEOPLE, QUESTS)

    people = [{**PEOPLE[0], "name": "Otro", "role": "Líder", "area": "Y", "is_newcomer": False}]
    quests = [{**QUESTS[0], "title": "Misión nueva", "points": 25}]
    sync_game_data(db_session, people, quests)

    person = db_session.scalar(select(Person).where(Person.key == "data-test-nuevo"))
    quest = db_session.scalar(select(QuestRow).where(QuestRow.key == "data-test-mision"))
    assert (person.name, person.role, person.area, person.is_newcomer) == (
        "Otro",
        "Líder",
        "Y",
        False,
    )
    assert (quest.title, quest.points) == ("Misión nueva", 25)
