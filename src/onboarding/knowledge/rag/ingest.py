"""Ingesta del corpus: lee corpus/, corta en fragmentos y los indexa.

Uso:
    docker compose run --rm app python -m onboarding.knowledge.rag corpus

Es idempotente: volver a correrlo sobre el mismo corpus no duplica fragmentos.
"""

import argparse
import logging
from pathlib import Path

from onboarding.knowledge.rag.chunking import chunk_text

logger = logging.getLogger(__name__)


def ingest_directory(path: Path) -> int:
    # README.md documenta la carpeta para el equipo; no es parte del corpus.
    documents = [doc for doc in sorted(path.glob("**/*.md")) if doc.name != "README.md"]
    if not documents:
        logger.warning("No hay documentos .md en %s", path)
        return 0

    total_chunks = 0
    for document in documents:
        chunks = chunk_text(document.read_text(encoding="utf-8"))
        total_chunks += len(chunks)
        logger.info("%s -> %s fragmentos", document.name, len(chunks))
        # TODO(rag): embeddings + guardado en pgvector, borrando antes los
        # fragmentos previos de ese documento (idempotencia).

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
