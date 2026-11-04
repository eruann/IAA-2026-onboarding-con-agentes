# producto
# Este archivo es parte del producto: el asistente de onboarding que se
# entrega y se evalúa.

"""Un único lugar donde se elige el modelo.

Cambiar de modelo es cambiar `LLM_MODEL` en el entorno; cambiar de proveedor es
cambiar `LLM_PROVIDER`. Los agentes reciben un chat model de LangChain y no
saben (ni tienen que saber) qué hay detrás.

Cada tarea pide el modelo por perfil, según lo que necesita (ADR 0014):

- principal (`get_chat_model`): conversar. Es `LLM_MODEL`.
- estructurado (`get_structured_model`): devolver datos con forma fija (salida
  estructurada), aunque el pedido sea largo. Es `LLM_STRUCTURED_MODEL` o, si está
  vacío, el principal que se esté usando.
- embeddings (`get_embeddings`): textos a vectores, para RAG. Lo elige el ADR 0005.

Modelos vía OpenRouter: "anthropic/claude-haiku-4.5", "openai/gpt-4o-mini",
"qwen/qwen-2.5-72b-instruct", "meta-llama/llama-3.3-70b-instruct:free", etc.
"""

from typing import get_args

from fastembed import TextEmbedding
from langchain_core.embeddings import Embeddings
from langchain_core.language_models import BaseChatModel, FakeListChatModel
from langchain_openai import ChatOpenAI
from pydantic import SecretStr

from onboarding.config import LLMProvider, Settings, get_settings
from onboarding.llm.callbacks import UsageLogger

# Modelo de embeddings (ADR 0005, cerrada): local vía fastembed (ONNX, sin
# torch), gratis, sin API key. `intfloat/multilingual-e5-small` no está en el
# registro de esta versión de fastembed (sí `multilingual-e5-large`, 1024 dim:
# mucho más pesado de lo que pide este corpus). 384 dimensiones.
EMBEDDINGS_MODEL = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"

# Respuestas del proveedor `fake`: determinísticas, sin red ni costo.
# Los tests que necesiten otra cosa pasan sus propias respuestas.
FAKE_RESPONSES = ["[fake] respuesta de prueba"]


# recorrido: modelo-llm
def get_chat_model(
    settings: Settings | None = None,
    *,
    provider: LLMProvider | None = None,
    model: str | None = None,
    temperature: float = 0.0,
    max_tokens: int = 1024,
) -> BaseChatModel:
    """`provider` y `model` pisan a LLM_PROVIDER y LLM_MODEL para esta llamada: así
    la interfaz deja elegir o comparar modelos sin tocar el .env. Las keys y las
    URLs siguen saliendo de la configuración."""
    settings = settings or get_settings()
    if provider is not None:
        settings = settings.model_copy(update={"llm_provider": provider})

    if settings.llm_provider == "fake":
        return FakeListChatModel(responses=FAKE_RESPONSES)

    if settings.llm_provider == "openrouter":
        if settings.openrouter_api_key is None:
            raise RuntimeError("Falta OPENROUTER_API_KEY (o usá LLM_PROVIDER=fake)")
        api_key = settings.openrouter_api_key
        base_url = settings.openrouter_base_url
    else:  # openai_compat: Ollama u otro proveedor compatible con OpenAI
        # Los servidores locales como Ollama ignoran la key, pero el cliente
        # exige una: sin key configurada se manda un valor de relleno.
        api_key = settings.openai_compat_api_key or SecretStr("sin-key")
        base_url = settings.openai_compat_base_url

    return ChatOpenAI(
        model=model or settings.llm_model,
        base_url=base_url,
        api_key=api_key,
        temperature=temperature,
        max_tokens=max_tokens,
        callbacks=[UsageLogger()],
    )


def _provider_and_model(value: str, default_provider: LLMProvider) -> tuple[LLMProvider, str]:
    """ "openrouter:google/gemma…" o solo "google/gemma…" (con el proveedor de siempre).
    Los nombres de modelo pueden tener ":" (":free"): solo cuenta si antes hay un
    proveedor conocido."""
    prefix, _, rest = value.partition(":")
    if rest and prefix in get_args(LLMProvider):
        return prefix, rest  # type: ignore[return-value]
    return default_provider, value


def get_structured_model(
    fallback: BaseChatModel | None = None, settings: Settings | None = None
) -> BaseChatModel:
    """El modelo del perfil estructurado: el de LLM_STRUCTURED_MODEL o, si está vacío,
    `fallback` (el principal que se esté usando; sin él, el de LLM_MODEL)."""
    settings = settings or get_settings()
    if not settings.llm_structured_model:
        return fallback or get_chat_model(settings)
    provider, model = _provider_and_model(settings.llm_structured_model, settings.llm_provider)
    return get_chat_model(settings, provider=provider, model=model)


class _FastEmbed(Embeddings):
    """`fastembed` con la interfaz `Embeddings` de LangChain. Carga perezosa: crear
    la instancia no descarga los pesos del modelo, recién el primer `embed_*`."""

    def __init__(self, model_name: str) -> None:
        self._model_name = model_name
        self._model: TextEmbedding | None = None

    def _loaded(self) -> TextEmbedding:
        if self._model is None:
            self._model = TextEmbedding(self._model_name)
        return self._model

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        return [vector.tolist() for vector in self._loaded().embed(texts)]

    def embed_query(self, text: str) -> list[float]:
        return self.embed_documents([text])[0]


_embeddings: Embeddings | None = None


def get_embeddings(settings: Settings | None = None) -> Embeddings:
    """El modelo de embeddings, para RAG (ADR 0005, cerrada). Uno solo para todo el
    sistema (no depende de `settings` hoy: el modelo es fijo, ver el ADR), cacheado
    acá para no recargarlo en cada llamada."""
    global _embeddings
    if _embeddings is None:
        _embeddings = _FastEmbed(EMBEDDINGS_MODEL)
    return _embeddings
