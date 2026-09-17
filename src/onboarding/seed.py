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


def seed(with_corpus: bool = True) -> None:
    people = load_yaml("people.yaml")
    quests = load_yaml("quests.yaml")
    rewards = load_yaml("rewards.yaml")
    logger.info("people=%s quests=%s rewards=%s", len(people), len(quests), len(rewards))

    # TODO(experiencia): insertar/actualizar por clave natural (upsert), nunca
    # insertar a ciegas: de ahí sale la idempotencia.

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
