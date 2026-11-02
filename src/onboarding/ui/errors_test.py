from onboarding.knowledge import who_knows_about
from onboarding.ui.errors import explain


class RateLimitError(Exception):
    pass


def test_un_todo_se_muestra_como_pendiente_con_su_archivo() -> None:
    try:
        who_knows_about("cámaras frías")
    except NotImplementedError as error:
        kind, message = explain(error)

    assert kind == "pending"
    assert "src/onboarding/knowledge/informal_network/queries.py" in message


def test_los_errores_del_proveedor_se_explican_en_castellano() -> None:
    kind, message = explain(RateLimitError("429"))

    assert kind == "error"
    assert "límite de uso gratis" in message


def test_un_modelo_sin_salida_estructurada_no_es_un_todo() -> None:
    kind, _ = explain(NotImplementedError("with_structured_output is not implemented"))

    assert kind == "error"


class OpenAIRateLimitError(Exception):
    pass


def test_reconoce_el_error_aunque_traiga_el_prefijo_del_proveedor() -> None:
    assert "límite de uso gratis" in explain(OpenAIRateLimitError("429"))[1]
