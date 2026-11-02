"""Lo escrito: ingesta, búsqueda y verificación de citas.

Parte de la knowledge layer. Titular: rol RAG y evaluación.
"""

from onboarding.knowledge.rag.chunking import chunk_text
from onboarding.knowledge.rag.citations import quote_is_supported
from onboarding.knowledge.rag.corpus import read_documents
from onboarding.knowledge.rag.ingest import ingest_directory
from onboarding.knowledge.rag.retriever import retrieve
from onboarding.knowledge.rag.workshop import WORKSHOP

# recorrido: rag-interfaz
__all__ = [
    "WORKSHOP",
    "chunk_text",
    "ingest_directory",
    "quote_is_supported",
    "read_documents",
    "retrieve",
]
