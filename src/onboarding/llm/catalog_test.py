import pytest

from onboarding.config import Settings
from onboarding.llm import catalog

OPENROUTER = {
    "data": [
        {"id": "google/gemma-4-31b-it:free", "architecture": {"output_modalities": ["text"]}},
        {"id": "qwen/qwen3:free", "architecture": {"output_modalities": ["text"]}},
        {"id": "google/lyria:free", "architecture": {"output_modalities": ["audio"]}},
        {"id": "anthropic/claude-haiku-4.5", "architecture": {"output_modalities": ["text"]}},
    ]
}
OLLAMA = {"data": [{"id": "gemma3:4b"}]}


@pytest.fixture(autouse=True)
def _sin_cache() -> None:
    catalog._cache.clear()


def _respuestas(monkeypatch: pytest.MonkeyPatch, *, openrouter=None, ollama=None) -> None:
    def get_json(url: str, timeout: float) -> dict:
        source = openrouter if "openrouter" in url else ollama
        if source is None:
            raise ConnectionError("no responde")
        return source

    monkeypatch.setattr(catalog, "_get_json", get_json)


def _settings(**kwargs) -> Settings:
    defaults = {
        "llm_provider": "openrouter",
        "llm_model": "google/gemma-4-31b-it:free",
        "openrouter_api_key": "sk-test",
    }
    return Settings(**(defaults | kwargs))


def test_el_del_env_va_primero_y_despues_los_gratis_de_texto(monkeypatch) -> None:
    _respuestas(monkeypatch, openrouter=OPENROUTER)

    options = catalog.available_models(_settings())

    assert [option.model for option in options] == ["google/gemma-4-31b-it:free", "qwen/qwen3:free"]
    assert options[0].label.endswith("(del .env)")


def test_suma_los_modelos_de_ollama_si_responde(monkeypatch) -> None:
    _respuestas(monkeypatch, openrouter=OPENROUTER, ollama=OLLAMA)

    options = catalog.available_models(_settings())

    assert options[-1] == catalog.ModelOption(
        "openai_compat", "gemma3:4b", "gemma3:4b · Ollama local"
    )


def test_si_nada_responde_queda_solo_el_del_env(monkeypatch) -> None:
    _respuestas(monkeypatch)

    assert [option.model for option in catalog.available_models(_settings())] == [
        "google/gemma-4-31b-it:free"
    ]


def test_sin_key_de_openrouter_no_lista_sus_modelos(monkeypatch) -> None:
    _respuestas(monkeypatch, openrouter=OPENROUTER)

    options = catalog.available_models(_settings(llm_provider="fake", openrouter_api_key=None))

    assert [option.provider for option in options] == ["fake"]
