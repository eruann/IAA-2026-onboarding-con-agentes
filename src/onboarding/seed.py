# producto
# Este archivo es parte del producto: el asistente de onboarding que se
# entrega y se evalúa.

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

from sqlalchemy.orm import Session

from onboarding.db.session import session_scope
from onboarding.game import check_quests, sync_game_data
from onboarding.knowledge import ingest_directory
from onboarding.paths import load_data_yaml

logger = logging.getLogger(__name__)


def seed(with_corpus: bool = True, session: Session | None = None) -> None:
    people = load_data_yaml("people.yaml")
    quests = load_data_yaml("quests.yaml")
    rewards = load_data_yaml("rewards.yaml")
    logger.info("people=%s quests=%s rewards=%s", len(people), len(quests), len(rewards))
    # Las mismas reglas que revisa el taller de Experiencia: se avisa, no se frena
    for quest, problems in zip(quests, check_quests(quests), strict=True):
        if problems:
            logger.warning("Misión %s: %s", quest.get("key", "?"), "; ".join(problems))

    with session_scope(session, commit=True) as db_session:
        sync_game_data(db_session, people, quests)

    if with_corpus:
        ingest_directory(session=session)


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    parser = argparse.ArgumentParser(description="Carga la empresa ficticia en la base")
    parser.add_argument("--sin-corpus", action="store_true", help="no reindexar los documentos")
    args = parser.parse_args()
    seed(with_corpus=not args.sin_corpus)


if __name__ == "__main__":
    main()
