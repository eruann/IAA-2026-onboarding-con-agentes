"""Búsqueda de fragmentos relevantes. Titular: rol RAG."""

from dataclasses import dataclass


@dataclass(frozen=True)
class RetrievedChunk:
    """Un fragmento recuperado, con lo necesario para citarlo."""

    text: str
    document: str  # nombre del archivo en corpus/
    section: str  # encabezado dentro del documento
    score: float


def retrieve(query: str, k: int = 5) -> list[RetrievedChunk]:
    # TODO(rag): búsqueda por similitud en pgvector.
    # Se mide precisión/recall aparte de la calidad de la respuesta, para poder
    # distinguir "no encontró el documento" de "encontró y respondió mal".
    raise NotImplementedError("TODO(rag): implementar búsqueda en pgvector")
