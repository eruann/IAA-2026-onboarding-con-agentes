import pytest
from langchain_core.language_models import FakeListChatModel

from onboarding.config import Settings
from onboarding.llm.factory import get_chat_model


def test_proveedor_fake_no_necesita_api_key() -> None:
    model = get_chat_model(Settings(llm_provider="fake"))

    assert isinstance(model, FakeListChatModel)


def test_openrouter_sin_api_key_falla_con_mensaje_claro() -> None:
    with pytest.raises(RuntimeError, match="OPENROUTER_API_KEY"):
        get_chat_model(Settings(llm_provider="openrouter", openrouter_api_key=None))


def test_openrouter_con_api_key_vacia_falla_con_mensaje_claro() -> None:
    # Render deja las variables sin cargar como "": no puede pasar como key válida.
    with pytest.raises(RuntimeError, match="OPENROUTER_API_KEY"):
        get_chat_model(Settings(llm_provider="openrouter", openrouter_api_key=""))


def test_openai_compat_sin_api_key_usa_valor_de_relleno() -> None:
    # Ollama no necesita key, pero el cliente de OpenAI exige una.
    model = get_chat_model(Settings(llm_provider="openai_compat", openai_compat_api_key=""))

    assert model.openai_api_key.get_secret_value() == "sin-key"


def test_openrouter_usa_su_base_url_y_el_modelo_configurado() -> None:
    settings = Settings(
        llm_provider="openrouter",
        openrouter_api_key="sk-test",
        llm_model="qwen/qwen-2.5-72b-instruct",
    )

    model = get_chat_model(settings)

    assert model.model_name == "qwen/qwen-2.5-72b-instruct"
    assert "openrouter.ai" in str(model.openai_api_base)
