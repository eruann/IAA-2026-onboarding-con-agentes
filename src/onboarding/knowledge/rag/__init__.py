# producto
# Este archivo es parte del producto: el asistente de onboarding que se
# entrega y se evalúa.

"""Lo escrito: ingesta, búsqueda y verificación de citas.

Parte de la knowledge layer. Titular: rol RAG y evaluación. Su agente y su taller
están en agents/answer_question/.
"""

from onboarding.knowledge.rag.chunking import (
    DEFAULT_MAX_CHARS,
    DEFAULT_OVERLAP,
    Chunk,
    chunk_text,
)
from onboarding.knowledge.rag.citations import quote_is_supported
from onboarding.knowledge.rag.corpus import document_names, read_documents
from onboarding.knowledge.rag.ingest import ingest_directory
from onboarding.knowledge.rag.retriever import RetrievedChunk, retrieve

# recorrido: rag-interfaz
__all__ = [
    "Chunk",
    "DEFAULT_MAX_CHARS",
    "DEFAULT_OVERLAP",
    "RetrievedChunk",
    "chunk_text",
    "document_names",
    "ingest_directory",
    "quote_is_supported",
    "read_documents",
    "retrieve",
]
