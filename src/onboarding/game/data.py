# producto
# Este archivo es parte del producto: el asistente de onboarding que se
# entrega y se evalúa.

"""Carga las personas y misiones de data/*.yaml en las tablas del juego.

La usa el seed. Es idempotente: actualiza por `key` y no duplica asignaciones.
"""

from sqlalchemy import select
from sqlalchemy.orm import Session

from onboarding.game.models import Person, QuestAssignment, QuestRow


def sync_game_data(session: Session, people: list[dict], quests: list[dict]) -> None:
    """Personas y misiones a la base; cada ingresante queda con todas las misiones."""
    people_by_key = {person.key: person for person in session.scalars(select(Person)).all()}
    for data in people:
        person = people_by_key.get(data["key"])
        if person is None:
            person = Person(key=data["key"])
            session.add(person)
            people_by_key[person.key] = person
        person.name = data["name"]
        person.role = data["role"]
        person.area = data["area"]
        person.is_newcomer = data["is_newcomer"]

    quests_by_key = {quest.key: quest for quest in session.scalars(select(QuestRow)).all()}
    for data in quests:
        quest = quests_by_key.get(data["key"])
        if quest is None:
            quest_fields = {key: value for key, value in data.items() if key != "key"}
            quest = QuestRow(key=data["key"], **quest_fields)
            session.add(quest)
            quests_by_key[quest.key] = quest
        else:
            for key, value in data.items():
                if key != "key":
                    setattr(quest, key, value)

    session.flush()
    newcomers = session.scalars(select(Person).where(Person.is_newcomer.is_(True))).all()
    existing_assignments = set(
        session.execute(select(QuestAssignment.person_id, QuestAssignment.quest_id)).all()
    )
    for person in newcomers:
        for quest in quests_by_key.values():
            pair = (person.id, quest.id)
            if pair not in existing_assignments:
                session.add(QuestAssignment(person_id=person.id, quest_id=quest.id))
                existing_assignments.add(pair)
