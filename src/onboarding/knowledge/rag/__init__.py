"""Lo escrito: ingesta, búsqueda y verificación de citas.

Parte de la knowledge layer. Titular: rol RAG y evaluación.
"""

from onboarding.knowledge.rag.chunking import chunk_text
from onboarding.knowledge.rag.citations import quote_is_supported
from onboarding.knowledge.rag.ingest import ingest_directory
from onboarding.knowledge.rag.retriever import retrieve

__all__ = ["chunk_text", "ingest_directory", "quote_is_supported", "retrieve"]
