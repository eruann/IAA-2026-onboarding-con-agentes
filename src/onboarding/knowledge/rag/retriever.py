# producto
# Este archivo es parte del producto: el asistente de onboarding que se
# entrega y se evalúa.

"""Búsqueda de fragmentos relevantes. Titular: rol RAG."""

from dataclasses import dataclass

from sqlalchemy import select

from onboarding.db.session import session_scope
from onboarding.knowledge.rag.embeddings import embed_texts
from onboarding.knowledge.rag.models import Chunk, Document


@dataclass(frozen=True)
class RetrievedChunk:
    """Un fragmento recuperado, con lo necesario para citarlo."""

    text: str
    document: str  # nombre del archivo en corpus/
    section: str  # encabezado dentro del documento
    score: float


# recorrido: busqueda
def retrieve(query: str, k: int = 3) -> list[RetrievedChunk]:
    """Los `k` fragmentos más parecidos a `query`, por similitud de coseno en
    pgvector. `score` es la similitud (1 = idéntico, 0 = nada que ver).

    `k=3` por default: medido contra `eval/rag_questions.yaml` (ver ADR 0005),
    es donde el recall ya llegó a su máximo (92%); subirlo no trae más
    documentos correctos, solo diluye la precisión con fragmentos de otros
    documentos.

    Sin parámetro de sesión a propósito: esta función se expone tal cual en el
    taller de `/ui` (y en el de Diseñador de misiones) como una herramienta más,
    y esa interfaz solo sabe dibujar formularios para tipos simples (`str`,
    `int`, etc.), no para una `Session` de SQLAlchemy."""
    [query_vector] = embed_texts([query])
    distance = Chunk.embedding.cosine_distance(query_vector)

    with session_scope() as session:
        rows = session.execute(
            select(Chunk.text, Chunk.section, Document.path, distance.label("distance"))
            .join(Document, Chunk.document_id == Document.id)
            .order_by(distance)
            .limit(k)
        ).all()

    return [
        RetrievedChunk(text=text, document=path, section=section, score=1 - distance)
        for text, section, path, distance in rows
    ]
