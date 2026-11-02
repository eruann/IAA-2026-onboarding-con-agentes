"""Qué modelos se pueden elegir desde la interfaz.

El del .env va primero. Después, los gratis de OpenRouter (cambian seguido, por
eso se consultan en vivo y no se escriben en el código) y los que haya instalados
en Ollama. Si una fuente no responde, se saltea: la lista nunca falla.
"""

import json
import logging
import time
import urllib.request
from dataclasses import dataclass

from onboarding.config import LLMProvider, Settings, get_settings

logger = logging.getLogger(__name__)

# Las listas se guardan un rato: no hace falta preguntarle a OpenRouter cada vez
# que alguien abre la página.
CACHE_SECONDS = 300
_cache: dict[str, tuple[float, list[str]]] = {}


@dataclass(frozen=True)
class ModelOption:
    provider: LLMProvider
    model: str
    label: str


def _get_json(url: str, timeout: float) -> dict:
    with urllib.request.urlopen(url, timeout=timeout) as response:  # noqa: S310
        return json.load(response)


def _cached(key: str, fetch) -> list[str]:
    now = time.monotonic()
    if key in _cache and now - _cache[key][0] < CACHE_SECONDS:
        return _cache[key][1]
    try:
        models = fetch()
    except Exception as error:  # sin red, Ollama cerrado, respuesta rara
        logger.info("No se pudo listar modelos de %s: %s", key, error)
        models = []
    _cache[key] = (now, models)
    return models


def free_openrouter_models(settings: Settings) -> list[str]:
    """Modelos gratis de OpenRouter que reciben y devuelven texto."""

    def fetch() -> list[str]:
        data = _get_json(f"{settings.openrouter_base_url}/models", timeout=5)["data"]
        return sorted(
            item["id"]
            for item in data
            if item["id"].endswith(":free")
            and item.get("architecture", {}).get("output_modalities", ["text"]) == ["text"]
        )

    return _cached("openrouter", fetch)


def ollama_models(settings: Settings) -> list[str]:
    """Modelos instalados en el Ollama de OPENAI_COMPAT_BASE_URL."""

    def fetch() -> list[str]:
        data = _get_json(f"{settings.openai_compat_base_url}/models", timeout=1)["data"]
        return sorted(item["id"] for item in data)

    return _cached("ollama", fetch)


# recorrido: modelos-elegibles
def available_models(settings: Settings | None = None) -> list[ModelOption]:
    settings = settings or get_settings()
    default = ModelOption(
        settings.llm_provider, settings.llm_model, f"{settings.llm_model} (del .env)"
    )
    if settings.llm_provider == "fake":
        default = ModelOption("fake", "fake", "fake (respuestas fijas, sin red)")

    options = [default]
    if settings.openrouter_api_key is not None:
        options += [
            ModelOption("openrouter", model, f"{model} · OpenRouter")
            for model in free_openrouter_models(settings)
            if model != default.model
        ]
    options += [
        ModelOption("openai_compat", model, f"{model} · Ollama local")
        for model in ollama_models(settings)
    ]
    return options
