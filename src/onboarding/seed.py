"""Carga los datos de la empresa ficticia en la base.

    docker compose run --rm app python -m onboarding.seed

Es idempotente: correrlo dos veces deja la base igual que correrlo una.
Hace falta porque hay más de una base: la local de cada integrante, la de CI
(que arranca vacía en cada corrida) y la de la demo.

Los datos viven en data/*.yaml y el corpus en corpus/*.md: los escribe quien
arma la empresa ficticia, sin tocar este archivo.
"""

import argparse
import logging
from pathlib import Path

import yaml
from sqlalchemy import select
from sqlalchemy.orm import Session

from onboarding.db.session import get_engine
from onboarding.game.models import Person, QuestAssignment, QuestRow
from onboarding.knowledge import ingest_directory

logger = logging.getLogger(__name__)

DATA_DIR = Path("data")
CORPUS_DIR = Path("corpus")


def load_yaml(name: str) -> list[dict]:
    path = DATA_DIR / name
    if not path.exists():
        logger.warning("Falta %s: se saltea", path)
        return []
    return yaml.safe_load(path.read_text(encoding="utf-8")) or []


def _load_game_data(session: Session, people: list[dict], quests: list[dict]) -> None:
    people_by_name = {person.name: person for person in session.scalars(select(Person)).all()}
    for data in people:
        person = people_by_name.get(data["name"])
        if person is None:
            person = Person(name=data["name"], role=data["role"], area=data["area"])
            session.add(person)
            people_by_name[person.name] = person
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


def seed(with_corpus: bool = True, session: Session | None = None) -> None:
    people = load_yaml("people.yaml")
    quests = load_yaml("quests.yaml")
    rewards = load_yaml("rewards.yaml")
    logger.info("people=%s quests=%s rewards=%s", len(people), len(quests), len(rewards))

    if session is None:
        with Session(get_engine()) as db_session, db_session.begin():
            _load_game_data(db_session, people, quests)
    else:
        _load_game_data(session, people, quests)

    if with_corpus:
        ingest_directory(CORPUS_DIR)


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    parser = argparse.ArgumentParser(description="Carga la empresa ficticia en la base")
    parser.add_argument("--sin-corpus", action="store_true", help="no reindexar los documentos")
    args = parser.parse_args()
    seed(with_corpus=not args.sin_corpus)


if __name__ == "__main__":
    main()
