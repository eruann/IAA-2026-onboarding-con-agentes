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

from langchain_anthropic import ChatAnthropic
from langchain_core.embeddings import Embeddings
from langchain_core.language_models import BaseChatModel, FakeListChatModel
from langchain_openai import ChatOpenAI
from pydantic import SecretStr

from onboarding.config import LLMProvider, Settings, get_settings
from onboarding.llm.callbacks import UsageLogger

# Respuestas del proveedor `fake`: determinísticas, sin red ni costo.
# Los tests que necesiten otra cosa pasan sus propias respuestas.
FAKE_RESPONSES = ["[fake] respuesta de prueba"]
# Tope de salida mínimo para Claude directo: deja lugar al razonamiento y a la respuesta
ANTHROPIC_MIN_TOKENS = 16000


# recorrido: modelo-llm
def get_chat_model(
    settings: Settings | None = None,
    *,
    provider: LLMProvider | None = None,
    model: str | None = None,
    temperature: float = 0.0,
    max_tokens: int = 1024,
    reasoning: bool = False,
) -> BaseChatModel:
    """`provider` y `model` pisan a LLM_PROVIDER y LLM_MODEL para esta llamada: así
    la interfaz deja elegir o comparar modelos sin tocar el .env. Las keys y las
    URLs siguen saliendo de la configuración.

    `reasoning` prende el razonamiento de Claude directo (en los demás proveedores
    razona el modelo si sabe). Es para el perfil estructurado: la salida es un JSON
    y los bloques de razonamiento no llegan a nadie."""
    settings = settings or get_settings()
    if provider is not None:
        settings = settings.model_copy(update={"llm_provider": provider})

    if settings.llm_provider == "fake":
        return FakeListChatModel(responses=FAKE_RESPONSES)

    if settings.llm_provider == "anthropic":
        if settings.anthropic_api_key is None:
            raise RuntimeError("Falta ANTHROPIC_API_KEY (o usá otro proveedor)")
        # Claude 5 no acepta temperature: se usa la del modelo. Para conversar, el
        # razonamiento va apagado: con él, la respuesta llega como lista de bloques
        # (thinking + texto) y ask_model la muestra tal cual. Para datos estructurados
        # va prendido, adaptativo (el modelo decide cuánto pensar; Claude 5 no acepta
        # un presupuesto fijo): extrae mejor los casos dudosos. El tope alto es por
        # eso, porque el razonamiento cuenta en max_tokens. Sonnet y Opus 5.5 no se
        # dejan apagar (error 400 con "disabled"): para conversar van sin el parámetro,
        # con el adaptativo de fábrica.
        name = model or settings.llm_model
        thinking = {"type": "adaptive"} if reasoning else {"type": "disabled"}
        extra = {"thinking": thinking} if reasoning or "haiku" in name else {}
        return ChatAnthropic(
            model=name,
            api_key=settings.anthropic_api_key,
            max_tokens=max(max_tokens, ANTHROPIC_MIN_TOKENS),
            callbacks=[UsageLogger()],
            **extra,
        )

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
    `fallback` (el principal que se esté usando; sin él, el de LLM_MODEL). Con Claude
    directo, con razonamiento (salvo `fallback`, que ya viene armado)."""
    settings = settings or get_settings()
    if not settings.llm_structured_model:
        return fallback or get_chat_model(settings, reasoning=True)
    provider, model = _provider_and_model(settings.llm_structured_model, settings.llm_provider)
    return get_chat_model(settings, provider=provider, model=model, reasoning=True)


def get_embeddings(settings: Settings | None = None) -> Embeddings:
    """El modelo de embeddings, para RAG. Ningún módulo lo instancia por su cuenta."""
    raise NotImplementedError("TODO(rag): elegir el modelo de embeddings en el ADR 0005")
