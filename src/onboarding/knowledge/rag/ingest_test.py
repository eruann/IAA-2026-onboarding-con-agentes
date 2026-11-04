from pathlib import Path

import pytest
from sqlalchemy import select
from sqlalchemy.orm import Session

from onboarding.knowledge.rag.ingest import ingest_directory
from onboarding.knowledge.rag.models import Chunk, Document


@pytest.fixture
def corpus_dir(tmp_path: Path) -> Path:
    (tmp_path / "compras.md").write_text(
        "# Compras\n\n## Pedido de compra\n\nSe pide por el formulario interno.\n\n"
        "## Excepciones\n\nMenos de 50 dólares las autoriza el equipo.",
        encoding="utf-8",
    )
    return tmp_path


@pytest.mark.db
@pytest.mark.llm  # calcula embeddings reales (fastembed)
def test_ingesta_guarda_documento_y_fragmentos_con_su_seccion(
    corpus_dir: Path, db_session: Session
) -> None:
    total = ingest_directory(corpus_dir, session=db_session)

    assert total == 2
    document = db_session.scalar(select(Document).where(Document.path == "compras.md"))
    assert document is not None
    chunks = db_session.scalars(select(Chunk).where(Chunk.document_id == document.id)).all()
    assert {chunk.section for chunk in chunks} == {"Pedido de compra", "Excepciones"}
    assert all(len(chunk.embedding) == 384 for chunk in chunks)


@pytest.mark.db
@pytest.mark.llm
def test_reingestar_sin_cambios_no_duplica_fragmentos(
    corpus_dir: Path, db_session: Session
) -> None:
    ingest_directory(corpus_dir, session=db_session)

    total = ingest_directory(corpus_dir, session=db_session)

    document = db_session.scalar(select(Document).where(Document.path == "compras.md"))
    chunks = db_session.scalars(select(Chunk).where(Chunk.document_id == document.id)).all()
    assert total == 2
    assert len(chunks) == 2


@pytest.mark.db
@pytest.mark.llm
def test_reingestar_con_cambios_reemplaza_los_fragmentos_viejos(
    corpus_dir: Path, db_session: Session
) -> None:
    ingest_directory(corpus_dir, session=db_session)

    (corpus_dir / "compras.md").write_text(
        "# Compras\n\n## Única sección\n\nTexto nuevo y distinto.", encoding="utf-8"
    )
    ingest_directory(corpus_dir, session=db_session)

    document = db_session.scalar(select(Document).where(Document.path == "compras.md"))
    chunks = db_session.scalars(select(Chunk).where(Chunk.document_id == document.id)).all()
    assert [chunk.section for chunk in chunks] == ["Única sección"]
