"""Generación de embeddings.

DECISIÓN ABIERTA (ADR 0005, titular: rol RAG). Define la dimensión del vector,
o sea la tabla de chunks: no se puede crear esa tabla antes de elegir.

Opciones sobre la mesa:
  - modelo local en el contenedor: costo cero, sin API key, imagen más pesada
  - API de pago (Voyage, OpenAI): mejor calidad, imagen liviana, otra key y otro costo
  - OpenRouter NO sirve acá: no ofrece embeddings

Criterio de decisión: medir recall del retrieval con el set fijo de preguntas de
eval/rag_questions.yaml, no elegir por gusto.
"""

from collections.abc import Sequence


def embed_texts(texts: Sequence[str]) -> list[list[float]]:
    raise NotImplementedError("TODO(rag): ver ADR 0005 antes de implementar")
