import pytest
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


def test_get_embeddings_devuelve_siempre_la_misma_instancia() -> None:
    # Un solo modelo para todo el sistema (ADR 0005): no se recarga en cada llamada.
    assert get_embeddings() is get_embeddings()


@pytest.mark.llm  # descarga y corre el modelo de embeddings real
def test_get_embeddings_calcula_vectores_de_384_dimensiones() -> None:
    [vector] = get_embeddings().embed_documents(["texto de prueba"])

    assert len(vector) == 384
    assert get_embeddings().embed_query("texto de prueba") == vector
