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
embeddings.

A diferencia de los modelos `e5`, este no necesita prefijos distintos para
preguntas y para documentos: el mismo `embed_texts` sirve para ambos casos.
"""

from collections.abc import Sequence

from fastembed import TextEmbedding

MODEL_NAME = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
EMBEDDING_DIM = 384

_model: TextEmbedding | None = None


def _get_model() -> TextEmbedding:
    # Carga perezosa: importar este módulo no debe descargar los pesos del modelo.
    global _model
    if _model is None:
        _model = TextEmbedding(MODEL_NAME)
    return _model


# recorrido: embeddings
def embed_texts(texts: Sequence[str]) -> list[list[float]]:
    """Embeddings de `texts`, tanto preguntas como fragmentos del corpus."""
    return [vector.tolist() for vector in _get_model().embed(list(texts))]
