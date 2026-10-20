"""Ingesta del corpus: lee corpus/, corta en fragmentos y los indexa.

Uso:
    docker compose run --rm app python -m onboarding.knowledge.rag corpus

Es idempotente: volver a correrlo sobre el mismo corpus no duplica fragmentos
(borra los chunks previos de cada documento antes de insertar los nuevos).
"""

import argparse
import logging
from pathlib import Path

from sqlalchemy import delete
from sqlalchemy.orm import Session

from onboarding.db.session import get_engine
from onboarding.knowledge.rag.chunking import chunk_text
from onboarding.knowledge.rag.embeddings import embed_texts
from onboarding.knowledge.rag.models import Chunk

logger = logging.getLogger(__name__)


# recorrido: ingesta
def ingest_directory(path: Path) -> int:
    # README.md documenta la carpeta para el equipo; no es parte del corpus.
    documents = [doc for doc in sorted(path.glob("**/*.md")) if doc.name != "README.md"]
    if not documents:
        logger.warning("No hay documentos .md en %s", path)
        return 0

    total_chunks = 0
    with Session(get_engine()) as session:
        for document in documents:
            chunks = chunk_text(document.read_text(encoding="utf-8"))
            total_chunks += len(chunks)
            logger.info("%s -> %s fragmentos", document.name, len(chunks))

            # Idempotencia: borrar los chunks previos de ESTE documento antes
            # de insertar los nuevos, así correrlo dos veces no duplica nada.
            session.execute(delete(Chunk).where(Chunk.document == document.name))

            if chunks:
                vectors = embed_texts(chunks)
                for text, vector in zip(chunks, vectors, strict=True):
                    session.add(
                        Chunk(document=document.name, section=None, text=text, embedding=vector)
                    )

        session.commit()

    logger.info("%s documentos, %s fragmentos", len(documents), total_chunks)
    return total_chunks


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    parser = argparse.ArgumentParser(description="Ingesta del corpus de la empresa ficticia")
    parser.add_argument("path", type=Path, nargs="?", default=Path("corpus"))
    args = parser.parse_args()
    ingest_directory(args.path)


if __name__ == "__main__":
    main()
