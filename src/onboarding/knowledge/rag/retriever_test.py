"""Tests de retrieve() contra Postgres + Ollama reales.

Necesita ambos (Postgres para pgvector, Ollama para embeber la query con
bge-m3), por eso lleva las dos marcas: `db` y `llm`. Nunca corre en CI
(CI solo levanta Postgres, no Ollama) — correrlo local con
`docker compose up -d` y `pytest -m db`.

La tabla `chunks` ya tiene el corpus real ingerido (commiteado fuera de la
transacción de `db_session`), así que los tests no asumen una tabla vacía:
usan nombres de documento que no colisionan con el corpus real y filtran los
resultados a los propios antes de comparar.
"""

import pytest
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from onboarding.knowledge.rag.embeddings import embed_texts
from onboarding.knowledge.rag.models import Chunk
from onboarding.knowledge.rag.retriever import retrieve


def _seed(session: Session, documents: dict[str, str]) -> None:
    vectors = embed_texts(list(documents.values()))
    for (document, text), vector in zip(documents.items(), vectors, strict=True):
        session.add(Chunk(document=document, section=None, text=text, embedding=vector))
    session.flush()


def _total_chunks(session: Session) -> int:
    return session.execute(select(func.count()).select_from(Chunk)).scalar_one()


@pytest.mark.db
@pytest.mark.llm
def test_retrieve_ordena_por_parecido_al_documento_correcto_primero(db_session: Session) -> None:
    _seed(
        db_session,
        {
            "zzz-test-frutas.md": (
                "El mango y la piña son frutas tropicales que crecen en climas cálidos."
            ),
            "zzz-test-maquinaria.md": (
                "Una excavadora hidráulica se usa para mover tierra en obras de construcción."
            ),
        },
    )
    # k = toda la tabla, para no perder nuestros dos chunks si el corpus real
    # los deja rankeados más abajo.
    k = _total_chunks(db_session)

    results = retrieve("¿qué frutas tropicales existen?", k=k, session=db_session)
    own = [r for r in results if r.document.startswith("zzz-test-")]

    assert [r.document for r in own] == ["zzz-test-frutas.md", "zzz-test-maquinaria.md"]
    assert own[0].score > own[1].score


@pytest.mark.db
@pytest.mark.llm
def test_retrieve_respeta_el_limite_k(db_session: Session) -> None:
    _seed(
        db_session,
        {
            "zzz-test-proveedores.md": "Texto sobre proveedores y alta de proveedor nuevo.",
            "zzz-test-vacaciones.md": "Texto sobre vacaciones y licencias del personal.",
        },
    )

    results = retrieve("proveedores", k=1, session=db_session)

    assert len(results) == 1


@pytest.mark.db
@pytest.mark.llm
def test_retrieve_devuelve_resultados_ordenados_por_score_descendente(
    db_session: Session,
) -> None:
    results = retrieve("¿cómo es el día a día en la oficina?", k=5, session=db_session)

    scores = [r.score for r in results]
    assert scores == sorted(scores, reverse=True)
