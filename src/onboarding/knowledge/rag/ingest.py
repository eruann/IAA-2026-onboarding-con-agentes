# producto
# Este archivo es parte del producto: el asistente de onboarding que se
# entrega y se evalúa.

"""Ingesta del corpus: lee corpus/, corta en fragmentos y los indexa.

Uso:
    docker compose run --rm app python -m onboarding.knowledge.rag corpus

Es idempotente: volver a correrlo sobre el mismo corpus no duplica fragmentos.
"""

import argparse
import logging
from pathlib import Path

from onboarding.knowledge.rag.chunking import chunk_text
from onboarding.paths import CORPUS_DIR, markdown_documents

logger = logging.getLogger(__name__)


# recorrido: ingesta
def ingest_directory(path: Path = CORPUS_DIR) -> int:
    """Corta los documentos de `path` en fragmentos y los guarda.

    Hoy corta pero todavía no guarda: termina con NotImplementedError. Sin
    documentos, devuelve 0."""
    documents = markdown_documents(path)
    if not documents:
        logger.warning("No hay documentos .md en %s", path)
        return 0

    total_chunks = 0
    for document in documents:
        chunks = chunk_text(document.read_text(encoding="utf-8"))
        total_chunks += len(chunks)
        logger.info("%s -> %s fragmentos", document.name, len(chunks))

    logger.info("%s documentos, %s fragmentos", len(documents), total_chunks)
    # Ya corta; falta guardar. Mientras tanto avisa que está pendiente (el taller y
    # el seed lo muestran así) en vez de devolver un número como si hubiera guardado.
    raise NotImplementedError(
        "TODO(rag): embeddings + guardado en pgvector, borrando antes los fragmentos "
        "previos de cada documento (idempotencia)"
    )


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    parser = argparse.ArgumentParser(description="Ingesta del corpus de la empresa ficticia")
    parser.add_argument("path", type=Path, nargs="?", default=CORPUS_DIR)
    args = parser.parse_args()
    try:
        ingest_directory(args.path)
    except NotImplementedError as pending:
        logger.warning("Ingesta incompleta: %s", pending)


if __name__ == "__main__":
    main()
