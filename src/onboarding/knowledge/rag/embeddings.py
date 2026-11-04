# producto
# Este archivo es parte del producto: el asistente de onboarding que se
# entrega y se evalúa.

"""Generación de embeddings.

DECISIÓN (ADR 0005, titular: rol RAG, cerrada): modelo local vía `fastembed`
(ONNX, sin torch, imagen liviana). `intfloat/multilingual-e5-small` no está en
el registro de modelos soportados de esta versión de fastembed (sí
`multilingual-e5-large`, pero es 1024 dim — mucho más pesado para lo que
necesita este corpus); el elegido es
`sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2` (384
dimensiones, multilingüe, el liviano estándar para similitud semántica).
Gratis, sin API key, corre offline. OpenRouter no sirve acá: no ofrece
embeddings. A diferencia de los modelos `e5`, este no necesita prefijos
distintos para preguntas y para documentos.

El modelo se obtiene de `onboarding.llm.get_embeddings()`, como todo modelo
(regla 5): así cualquier otra parte que necesite embeddings usa el mismo.
"""

from collections.abc import Sequence

from onboarding.llm import get_embeddings

# La dimensión del vector que elige el modelo del ADR 0005: la usa models.py
# para la columna `embedding` de `chunks`.
EMBEDDING_DIM = 384


# recorrido: embeddings
def embed_texts(texts: Sequence[str]) -> list[list[float]]:
    """Embeddings de `texts`, tanto preguntas como fragmentos del corpus."""
    return get_embeddings().embed_documents(list(texts))
