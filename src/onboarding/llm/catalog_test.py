import pytest

from onboarding.config import Settings
from onboarding.llm import catalog


def _free(model_id: str, reasoning: bool = True, output: str = "text") -> dict:
    return {
        "id": model_id,
        "architecture": {"output_modalities": [output]},
        "supported_parameters": ["reasoning"] if reasoning else [],
    }


OPENROUTER = {
    "data": [
        _free("a/uno:free"),
        _free("b/dos:free"),
        _free("c/tres:free"),
        _free("d/sin-razonar:free", reasoning=False),
        _free("e/musica:free", output="audio"),
        {"id": "f/pago", "architecture": {"output_modalities": ["text"]}},
    ]
}
OLLAMA = {"data": [{"id": "gemma3:4b"}, {"id": "qwen3:8b"}]}


@pytest.fixture(autouse=True)
def _sin_cache() -> None:
    catalog._cache.clear()


@pytest.fixture
def responden(monkeypatch: pytest.MonkeyPatch) -> None:
    def get_json(url: str, timeout: float) -> dict:
        return OPENROUTER if "openrouter" in url else OLLAMA

    monkeypatch.setattr(catalog, "_get_json", get_json)


def _settings(**kwargs) -> Settings:
    # Listas vacías explícitas: si no, Settings toma las del .env de quien corre el test
    defaults = {
        "llm_provider": "openrouter",
        "llm_model": "a/uno:free",
        "openrouter_api_key": "sk-test",
        "openrouter_models": [],
        "ollama_models": [],
    }
    return Settings(**(defaults | kwargs))


def _models(options: list, provider: str) -> list[str]:
    """Los modelos ofrecidos de un proveedor, sin contar el del .env (va primero)."""
    return [option.model for option in options[1:] if option.provider == provider]


def test_el_del_env_va_primero_y_no_se_repite(responden) -> None:
    options = catalog.model_catalog(_settings()).options

    assert options[0].model == "a/uno:free"
    assert options[0].label.endswith("(del .env)")
    assert "a/uno:free" not in _models(options, "openrouter")


def test_la_lista_del_env_se_completa_con_gratis_que_razonan(monkeypatch, responden) -> None:
    monkeypatch.setattr(catalog, "MAX_OPENROUTER", 3)

    options = catalog.model_catalog(
        _settings(llm_model="x/otro:free", openrouter_models=["f/pago", "no/existe:free"])
    ).options

    # f/pago está en la lista y existe; no/existe se omite; se completa hasta 3 (el
    # del .env cuenta) con gratis de texto que razonan (no audio, no sin razonamiento)
    assert _models(options, "openrouter") == ["f/pago", "a/uno:free"]


def test_si_la_lista_pasa_el_tope_van_todos_los_de_la_lista(monkeypatch, responden) -> None:
    monkeypatch.setattr(catalog, "MAX_OPENROUTER", 2)

    options = catalog.model_catalog(
        _settings(
            llm_model="x/otro:free", openrouter_models=["c/tres:free", "b/dos:free", "f/pago"]
        )
    ).options

    assert _models(options, "openrouter") == ["c/tres:free", "b/dos:free", "f/pago"]


def test_ollama_muestra_los_de_la_lista_que_estan_instalados(responden) -> None:
    options = catalog.model_catalog(_settings(ollama_models=["gemma3:4b", "llama3:8b"])).options

    assert _models(options, "openai_compat") == ["gemma3:4b"]


def test_ollama_sin_lista_muestra_todos_los_instalados(responden) -> None:
    assert _models(catalog.model_catalog(_settings()).options, "openai_compat") == [
        "gemma3:4b",
        "qwen3:8b",
    ]


def test_si_nada_responde_queda_solo_el_del_env(monkeypatch) -> None:
    def falla(url: str, timeout: float) -> dict:
        raise ConnectionError("no responde")

    monkeypatch.setattr(catalog, "_get_json", falla)

    assert [option.model for option in catalog.model_catalog(_settings()).options] == ["a/uno:free"]


def test_sin_key_de_openrouter_no_lista_sus_modelos(responden) -> None:
    options = catalog.model_catalog(_settings(llm_provider="fake", openrouter_api_key=None)).options

    assert _models(options, "openrouter") == []


def test_las_listas_vacias_del_env_valen_como_lista_vacia() -> None:
    settings = Settings(openrouter_models="", ollama_models="")

    assert settings.openrouter_models == [] and settings.ollama_models == []


def test_el_del_env_cuenta_para_el_tope_si_es_de_openrouter(monkeypatch, responden) -> None:
    monkeypatch.setattr(catalog, "MAX_OPENROUTER", 2)

    options = catalog.model_catalog(_settings(llm_model="a/uno:free")).options

    assert [option.model for option in options if option.provider == "openrouter"] == [
        "a/uno:free",
        "b/dos:free",
    ]


def _notes(**kwargs) -> list[str]:
    return catalog.model_catalog(_settings(**kwargs)).notes


def test_avisa_los_modelos_de_la_lista_que_no_estan(responden) -> None:
    notes = _notes(openrouter_models=["no/existe:free"], ollama_models=["llama3:8b"])

    assert any("OPENROUTER_MODELS" in note and "no/existe:free" in note for note in notes)
    assert any("ollama pull llama3:8b" in note for note in notes)


def test_avisa_si_ollama_no_responde_y_hay_lista(monkeypatch) -> None:
    def get_json(url: str, timeout: float) -> dict:
        if "openrouter" in url:
            return OPENROUTER
        raise ConnectionError("cerrado")

    monkeypatch.setattr(catalog, "_get_json", get_json)

    assert any("ollama serve" in note for note in _notes(ollama_models=["gemma3:4b"]))
    catalog._cache.clear()
    assert _notes() == []  # sin lista de Ollama, que no responda no es un problema


def test_avisa_si_falta_la_key_de_openrouter(responden) -> None:
    assert any("OPENROUTER_API_KEY" in note for note in _notes(openrouter_api_key=None))


def test_sin_problemas_no_hay_avisos(responden) -> None:
    assert _notes(openrouter_models=["b/dos:free"], ollama_models=["gemma3:4b"]) == []
