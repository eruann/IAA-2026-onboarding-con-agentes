"""Un único lugar donde se elige el modelo.

Cambiar de modelo es cambiar `LLM_MODEL` en el entorno; cambiar de proveedor es
cambiar `LLM_PROVIDER`. Los agentes reciben un chat model de LangChain y no
saben (ni tienen que saber) qué hay detrás.

Modelos vía OpenRouter: "anthropic/claude-haiku-4.5", "openai/gpt-4o-mini",
"qwen/qwen-2.5-72b-instruct", "meta-llama/llama-3.3-70b-instruct:free", etc.
"""

from langchain_core.language_models import BaseChatModel, FakeListChatModel
from langchain_openai import ChatOpenAI
from pydantic import SecretStr

from onboarding.config import Settings, get_settings
from onboarding.llm.callbacks import UsageLogger

# Respuestas del proveedor `fake`: determinísticas, sin red ni costo.
# Los tests que necesiten otra cosa pasan sus propias respuestas.
FAKE_RESPONSES = ["[fake] respuesta de prueba"]


def get_chat_model(
    settings: Settings | None = None,
    *,
    temperature: float = 0.0,
    max_tokens: int = 1024,
) -> BaseChatModel:
    settings = settings or get_settings()

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
        model=settings.llm_model,
        base_url=base_url,
        api_key=api_key,
        temperature=temperature,
        max_tokens=max_tokens,
        callbacks=[UsageLogger()],
    )
