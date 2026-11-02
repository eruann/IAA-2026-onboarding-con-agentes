# andamiaje
# Este archivo es andamiaje: una ayuda para que el equipo de estudiantes
# construya, pruebe o entienda el producto (talleres, diagramas, guías).
# No es parte del producto.

"""Qué modelos se pueden elegir desde la interfaz.

Sale de dos listas del .env (OPENROUTER_MODELS y OLLAMA_MODELS), filtradas por lo
que de verdad está disponible:

- Primero el del .env (LLM_PROVIDER + LLM_MODEL).
- OpenRouter: los de la lista que existen hoy. Si son menos de MAX_OPENROUTER, se
  completa con gratis que razonan ("thinking") y no están en la lista; si la lista
  tiene más, van todos los de la lista.
- Ollama: los de la lista que estén instalados; sin lista, todos los instalados.

Si una fuente no responde, se saltea: la lista nunca falla.
"""

import json
import logging
import time
import urllib.request
from dataclasses import dataclass, field

from onboarding.config import LLMProvider, Settings, get_settings

logger = logging.getLogger(__name__)

# Tope de modelos de OpenRouter cuando hay que completar la lista del .env
MAX_OPENROUTER = 6
# Las respuestas se guardan un rato: no hace falta preguntarle a OpenRouter cada
# vez que alguien abre la página.
CACHE_SECONDS = 300
_cache: dict[str, tuple[float, list[dict] | None]] = {}


# Cómo se muestra cada proveedor en el selector: así se ve dónde corre el modelo
PROVIDER_NAMES = {"openrouter": "OpenRouter", "openai_compat": "Ollama local"}


def _option(provider: LLMProvider, model: str) -> "ModelOption":
    if provider == "fake":
        return ModelOption("fake", "fake", "fake (respuestas fijas, sin red)")
    return ModelOption(provider, model, f"{model} · {PROVIDER_NAMES[provider]}")


@dataclass(frozen=True)
class ModelOption:
    provider: LLMProvider
    model: str
    label: str


def _get_json(url: str, timeout: float) -> dict:
    with urllib.request.urlopen(url, timeout=timeout) as response:  # noqa: S310
        return json.load(response)


def _models(source: str, url: str, timeout: float) -> list[dict] | None:
    """Los modelos que publica `url` (formato OpenAI: {"data": [...]}), con caché.

    None si no respondió (sin red, Ollama cerrado): eso se avisa en la interfaz.
    """
    now = time.monotonic()
    if source in _cache and now - _cache[source][0] < CACHE_SECONDS:
        return _cache[source][1]
    try:
        models = _get_json(url, timeout)["data"]
    except Exception as error:  # cualquier falla de red o de formato: se avisa y se sigue
        logger.info("No se pudo listar modelos de %s: %s", source, error)
        models = None
    _cache[source] = (now, models)
    return models


def _is_free_thinking(model: dict) -> bool:
    return (
        model["id"].endswith(":free")
        and model.get("architecture", {}).get("output_modalities", ["text"]) == ["text"]
        and "reasoning" in model.get("supported_parameters", [])
    )


@dataclass(frozen=True)
class ModelCatalog:
    options: list[ModelOption]
    # Problemas de configuración para mostrar en la interfaz, en castellano
    notes: list[str] = field(default_factory=list)


def _openrouter(settings: Settings, exclude: str, limit: int, notes: list[str]) -> list[str]:
    if settings.openrouter_api_key is None:
        if settings.openrouter_models or settings.llm_provider == "openrouter":
            notes.append("Falta OPENROUTER_API_KEY en el .env: no se listan modelos de OpenRouter.")
        return []
    published = _models("openrouter", f"{settings.openrouter_base_url}/models", timeout=5)
    if published is None:
        notes.append("No se pudo consultar OpenRouter (¿hay internet?): sus modelos no aparecen.")
        return []

    available = {model["id"] for model in published}
    missing = [model for model in settings.openrouter_models if model not in available]
    if missing:
        notes.append(
            "Están en OPENROUTER_MODELS pero OpenRouter no los tiene hoy: " + ", ".join(missing)
        )
    listed = [m for m in settings.openrouter_models if m in available and m != exclude]
    extra = [
        model["id"]
        for model in published
        if _is_free_thinking(model) and model["id"] not in listed and model["id"] != exclude
    ]
    return listed + extra[: max(0, limit - len(listed))]


def _ollama(settings: Settings, exclude: str, notes: list[str]) -> list[str]:
    published = _models("ollama", f"{settings.openai_compat_base_url}/models", timeout=1)
    if published is None:
        if settings.ollama_models or settings.llm_provider == "openai_compat":
            notes.append(
                f"Ollama no responde en {settings.openai_compat_base_url}: "
                "¿está corriendo `ollama serve`? (ver docs/setup.md)"
            )
        return []

    installed = [model["id"] for model in published]
    missing = [model for model in settings.ollama_models if model not in installed]
    if missing:
        notes.append(
            "Están en OLLAMA_MODELS pero no están instalados: "
            + ", ".join(f"{model} (`ollama pull {model}`)" for model in missing)
        )
    if settings.ollama_models:
        installed = [model for model in settings.ollama_models if model in installed]
    return [model for model in installed if model != exclude]


# recorrido: modelos-elegibles
def model_catalog(settings: Settings | None = None) -> ModelCatalog:
    settings = settings or get_settings()
    # El del .env va primero: es el que aparece elegido al abrir la página
    default = _option(settings.llm_provider, settings.llm_model)

    notes: list[str] = []
    # El del .env cuenta para el tope si también es de OpenRouter
    limit = MAX_OPENROUTER - (default.provider == "openrouter")
    options = [default]
    options += [
        _option("openrouter", model) for model in _openrouter(settings, default.model, limit, notes)
    ]
    options += [
        _option("openai_compat", model) for model in _ollama(settings, default.model, notes)
    ]
    return ModelCatalog(options, notes)
