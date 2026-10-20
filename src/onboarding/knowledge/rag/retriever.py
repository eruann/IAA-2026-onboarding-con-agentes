"""Búsqueda de fragmentos relevantes. Titular: rol RAG."""

from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.orm import Session

from onboarding.config import Settings
from onboarding.db.session import get_engine
from onboarding.knowledge.rag.embeddings import embed_texts
from onboarding.knowledge.rag.models import Chunk


@dataclass(frozen=True)
class RetrievedChunk:
    """Un fragmento recuperado, con lo necesario para citarlo."""

    text: str
    document: str  # nombre del archivo en corpus/
    section: str | None  # encabezado dentro del documento; ver models.py
    score: float


# recorrido: busqueda
def retrieve(
    query: str,
    k: int = 5,
    session: Session | None = None,
    settings: Settings | None = None,
) -> list[RetrievedChunk]:
    """Busca los `k` fragmentos más parecidos a `query` por distancia coseno.

    `score` es similitud (1 - distancia coseno): más alto es más parecido.
    Se mide precisión/recall aparte de la calidad de la respuesta, para poder
    distinguir "no encontró el documento" de "encontró y respondió mal" —
    ver eval/rag_questions.yaml.
    """
    [query_vector] = embed_texts([query], settings=settings)

    owns_session = session is None
    session = session or Session(get_engine())
    try:
        distance = Chunk.embedding.cosine_distance(query_vector)
        rows = session.execute(
            select(Chunk, distance.label("distance")).order_by(distance).limit(k)
        ).all()
    finally:
        if owns_session:
            session.close()

    return [
        RetrievedChunk(
            text=chunk.text,
            document=chunk.document,
            section=chunk.section,
            score=1 - distance,
        )
        for chunk, distance in rows
    ]
