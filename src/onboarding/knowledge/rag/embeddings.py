"""Generación de embeddings.

Modelo: `bge-m3` vía Ollama, decidido en ADR 0005. A diferencia de `LLM_MODEL`
(que sí es configurable por entorno), este modelo queda fijo acá a propósito:
cambiarlo implica una migración nueva y reindexar todo el corpus, no es un
switch de variable de entorno.

Reutiliza la misma configuración que `llm/factory.py` usa para el chat local
(`openai_compat_base_url`/`openai_compat_api_key`) — mismo contenedor de
Ollama, perfil `local-llm` en docker-compose.yml.
"""

from collections.abc import Sequence

from langchain_openai import OpenAIEmbeddings

from onboarding.config import Settings, get_settings

EMBEDDING_MODEL = "bge-m3"


# recorrido: embeddings
def embed_texts(texts: Sequence[str], settings: Settings | None = None) -> list[list[float]]:
    settings = settings or get_settings()

    client = OpenAIEmbeddings(
        model=EMBEDDING_MODEL,
        base_url=settings.openai_compat_base_url,
        api_key=settings.openai_compat_api_key,
        # Ollama espera texto plano, no tokens pre-convertidos. Desactivamos
        # toda la lógica de tokenización/chunking por límite de contexto (sea
        # con tiktoken o con transformers) — nuestros textos son chicos, no
        # hace falta trocearlos, y evita agregar transformers como dependencia.
        check_embedding_ctx_length=False,
    )
    return client.embed_documents(list(texts))
