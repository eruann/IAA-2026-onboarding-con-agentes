# producto
# Este archivo es parte del producto: el asistente de onboarding que se
# entrega y se evalúa.

"""Knowledge layer: lo que la organización sabe, en un solo lugar.

Dos fuentes, una sola puerta:

- `rag`: lo que está escrito (manuales, políticas, procesos). Titular: rol RAG.
- `informal_network`: lo que no está escrito ni figura en el organigrama: quién
  sabe de qué y a quién se consulta de verdad. Titular: rol Grafo cultural y datos.

Por ahora la capa se construye y se usa para el onboarding, pero no depende de
él: `game`, `bot` y `api` no forman parte de la capa, la consumen.

Reglas:
  - Fuera de la capa se importa SOLO desde acá: `from onboarding.knowledge import retrieve`.
  - Adentro, `rag` e `informal_network` pueden usarse por su interfaz pública
    (por ejemplo, para cruzar un proceso documentado con la persona que lo
    maneja). Se relacionan por clave, sin foreign keys entre sus tablas.
"""

from onboarding.knowledge.informal_network import KnowledgeTriple, Relation, who_knows_about
from onboarding.knowledge.rag import (
    DEFAULT_MAX_CHARS,
    DEFAULT_OVERLAP,
    chunk_text,
    document_names,
    ingest_directory,
    quote_is_supported,
    read_documents,
    retrieve,
)

# recorrido: knowledge-interfaz
__all__ = [
    # Lo escrito
    "DEFAULT_MAX_CHARS",
    "DEFAULT_OVERLAP",
    "chunk_text",
    "document_names",
    "ingest_directory",
    "quote_is_supported",
    "read_documents",
    "retrieve",
    # Lo no escrito
    "KnowledgeTriple",
    "Relation",
    "who_knows_about",
]
