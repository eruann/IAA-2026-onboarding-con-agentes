# producto
# Este archivo es parte del producto: el asistente de onboarding que se
# entrega y se evalúa.

"""Ingesta del corpus: lee corpus/, corta en fragmentos y los indexa.

Uso:
    docker compose run --rm app python -m onboarding.knowledge.rag corpus

Es idempotente: un documento que no cambió (mismo hash) no se reingesta. Uno
que cambió borra sus fragmentos viejos antes de guardar los nuevos.
"""

import argparse
import hashlib
import logging
from pathlib import Path

from sqlalchemy import delete, func, select
from sqlalchemy.orm import Session

from onboarding.db.session import session_scope
from onboarding.knowledge.rag.chunking import chunk_text
from onboarding.knowledge.rag.embeddings import embed_texts
from onboarding.knowledge.rag.models import Chunk, Document
from onboarding.paths import CORPUS_DIR, markdown_documents

logger = logging.getLogger(__name__)


def _hash(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


# recorrido: ingesta
def ingest_directory(path: Path = CORPUS_DIR, session: Session | None = None) -> int:
    """Corta los documentos de `path` en fragmentos, calcula sus embeddings y
    los guarda. Devuelve cuántos fragmentos quedaron indexados (nuevos o ya
    estaban). Sin documentos, devuelve 0."""
    documents = markdown_documents(path)
    if not documents:
        logger.warning("No hay documentos .md en %s", path)
        return 0

    total_chunks = 0
    with session_scope(session, commit=True) as session:
        for document_path in documents:
            doc_name = document_path.relative_to(path).as_posix()
            text = document_path.read_text(encoding="utf-8")
            content_hash = _hash(text)

            existing = session.scalar(select(Document).where(Document.path == doc_name))
            if existing is not None and existing.content_hash == content_hash:
                count = session.scalar(
                    select(func.count()).select_from(Chunk).where(Chunk.document_id == existing.id)
                )
                total_chunks += count or 0
                logger.info("%s sin cambios, no se reingesta", doc_name)
                continue

            chunks = chunk_text(text)
            if existing is None:
                existing = Document(path=doc_name, content_hash=content_hash)
                session.add(existing)
                session.flush()  # necesita existing.id para los chunks
            else:
                session.execute(delete(Chunk).where(Chunk.document_id == existing.id))
                existing.content_hash = content_hash

            vectors = embed_texts([chunk.text for chunk in chunks])
            session.add_all(
                Chunk(
                    document_id=existing.id,
                    section=chunk.section,
                    text=chunk.text,
                    embedding=vector,
                )
                for chunk, vector in zip(chunks, vectors, strict=True)
            )
            total_chunks += len(chunks)
            logger.info("%s -> %s fragmentos", doc_name, len(chunks))

    logger.info("%s documentos, %s fragmentos", len(documents), total_chunks)
    return total_chunks


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    parser = argparse.ArgumentParser(description="Ingesta del corpus de la empresa ficticia")
    parser.add_argument("path", type=Path, nargs="?", default=CORPUS_DIR)
    args = parser.parse_args()
    ingest_directory(args.path)


if __name__ == "__main__":
    main()
