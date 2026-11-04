from collections.abc import Iterator
from pathlib import Path

import pytest
from sqlalchemy import delete

from onboarding.db.session import session_scope
from onboarding.knowledge.rag.ingest import ingest_directory
from onboarding.knowledge.rag.models import Document
from onboarding.knowledge.rag.retriever import retrieve

# `retrieve` no acepta una sesión de test (ver retriever.py): estos tests
# ingestan y leen contra la base real, y limpian lo que indexaron al salir.
# Texto parafraseado a propósito (no calcado de corpus/compras.md ni
# corpus/vacaciones-y-licencias.md): si el corpus real ya está indexado, un
# texto casi idéntico podría empatarle el primer puesto a este fragmento de
# prueba y volver flaky el test.
DOCS = {
    "retriever-test-mascotas.md": (
        "# Mascotas\n\n## Llevar la mascota a la oficina\n\n"
        "No está permitido traer perros, gatos ni otros animales a ninguna sede de la empresa."
    ),
    "retriever-test-bicicletas.md": (
        "# Bicicletas\n\n## Estacionamiento de bicicletas\n\n"
        "Hay un bicicletero techado en la entrada lateral, con capacidad para veinte bicicletas."
    ),
}


@pytest.fixture
def indexed_corpus(tmp_path: Path) -> Iterator[None]:
    for name, text in DOCS.items():
        (tmp_path / name).write_text(text, encoding="utf-8")
    ingest_directory(tmp_path)
    try:
        yield
    finally:
        with session_scope(commit=True) as session:
            session.execute(delete(Document).where(Document.path.in_(DOCS)))


@pytest.mark.db
@pytest.mark.llm  # calcula el embedding real de la pregunta
@pytest.mark.usefixtures("indexed_corpus")
def test_trae_el_documento_y_la_seccion_mas_parecidos() -> None:
    # k grande y filtrado a nuestros propios documentos: en una base compartida
    # con el corpus real ya ingestado, algo de ahí puede ganarle el primer
    # puesto global a un fragmento de prueba de dos líneas. Lo que importa acá
    # es el orden relativo entre nuestros dos documentos, no el ranking global.
    results = retrieve("¿Puedo traer a mi perro al trabajo?", k=20)
    ours = [chunk for chunk in results if chunk.document in DOCS]

    assert ours[0].document == "retriever-test-mascotas.md"
    assert ours[0].section == "Llevar la mascota a la oficina"
    assert 0.0 < ours[0].score <= 1.0


@pytest.mark.db
@pytest.mark.llm
@pytest.mark.usefixtures("indexed_corpus")
def test_devuelve_hasta_k_resultados_ordenados_por_similitud() -> None:
    results = retrieve("dónde dejo la bici", k=2)

    assert len(results) == 2
    assert results[0].score >= results[1].score
