import pytest
from langchain_anthropic import ChatAnthropic
from langchain_core.language_models import FakeListChatModel

from onboarding.config import Settings
from onboarding.llm.factory import get_chat_model, get_embeddings, get_structured_model


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


def test_anthropic_sin_api_key_falla_con_mensaje_claro() -> None:
    with pytest.raises(RuntimeError, match="ANTHROPIC_API_KEY"):
        get_chat_model(Settings(llm_provider="anthropic", anthropic_api_key=""))


def test_anthropic_usa_su_cliente_y_el_modelo_elegido() -> None:
    settings = Settings(llm_provider="fake", anthropic_api_key="sk-ant-test")

    model = get_chat_model(settings, provider="anthropic", model="claude-haiku-5-5")

    assert isinstance(model, ChatAnthropic)
    assert model.model == "claude-haiku-5-5"
    # El razonamiento cuenta en max_tokens: con el tope por defecto no llega a responder
    assert model.max_tokens >= 16000
    # Apagado: si no, la respuesta llega en bloques y el chat los muestra crudos
    assert model.thinking == {"type": "disabled"}


def test_el_modelo_estructurado_de_anthropic_razona() -> None:
    settings = Settings(
        llm_provider="anthropic",
        anthropic_api_key="sk-ant-test",
        llm_model="claude-haiku-5-5",
        llm_structured_model="anthropic:claude-haiku-5-5",
    )

    # Para datos estructurados, prendido (adaptativo); para conversar, apagado
    assert get_structured_model(settings=settings).thinking == {"type": "adaptive"}
    assert get_chat_model(settings).thinking == {"type": "disabled"}


@pytest.mark.parametrize("name", ["claude-sonnet-5-5", "claude-opus-5-5"])
def test_sonnet_y_opus_no_reciben_razonamiento_apagado(name: str) -> None:
    # No lo aceptan (error 400): para conversar van con el adaptativo de fábrica
    settings = Settings(llm_provider="anthropic", anthropic_api_key="sk-ant-test")

    assert get_chat_model(settings, model=name).thinking is None
    assert get_chat_model(settings, model=name, reasoning=True).thinking == {"type": "adaptive"}


def test_el_modelo_y_el_proveedor_se_pueden_elegir_por_llamada() -> None:
    settings = Settings(
        llm_provider="fake",
        openrouter_api_key="sk-test",
        llm_model="google/gemma-4-31b-it:free",
    )

    model = get_chat_model(settings, provider="openrouter", model="qwen/qwen3:free")

    assert model.model_name == "qwen/qwen3:free"
    assert "openrouter.ai" in str(model.openai_api_base)


def test_sin_modelo_estructurado_se_usa_el_principal_que_se_este_usando() -> None:
    principal = FakeListChatModel(responses=["x"])

    assert get_structured_model(principal, Settings(llm_structured_model="")) is principal
    default = get_structured_model(settings=Settings(llm_provider="fake"))
    assert isinstance(default, FakeListChatModel)


def test_el_modelo_estructurado_puede_ser_de_otro_proveedor() -> None:
    settings = Settings(
        llm_provider="fake",
        openrouter_api_key="sk-test",
        llm_structured_model="openrouter:nvidia/nemotron-3-ultra:free",
    )

    model = get_structured_model(FakeListChatModel(responses=["x"]), settings)

    assert model.model_name == "nvidia/nemotron-3-ultra:free"
    assert "openrouter.ai" in str(model.openai_api_base)


def test_el_modelo_estructurado_sin_proveedor_usa_el_de_siempre() -> None:
    # El ":free" del nombre no se confunde con un proveedor
    settings = Settings(
        llm_provider="openrouter",
        openrouter_api_key="sk-test",
        llm_structured_model="google/gemma-4-31b-it:free",
    )

    assert get_structured_model(settings=settings).model_name == "google/gemma-4-31b-it:free"


def test_los_embeddings_todavia_son_pendientes() -> None:
    with pytest.raises(NotImplementedError, match=r"TODO\(rag\)"):
        get_embeddings()
