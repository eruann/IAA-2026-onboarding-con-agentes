from typing import Literal

import pytest
from langchain_core.language_models import BaseChatModel

from onboarding.workshop import (
    ChatHistory,
    all_workshops,
    describe_params,
    is_pending,
    markdown_table,
)


def _ejemplo(
    texto: str,
    cantidad: int = 3,
    umbral: float = 0.5,
    exacto: bool = False,
    modo: Literal["rápido", "lento"] = "rápido",
    model: BaseChatModel | None = None,
) -> str:
    return texto


def _pendiente() -> None:
    """Docstring antes del raise: sigue contando como pendiente."""
    raise NotImplementedError("TODO(rol): algo")


def _con_raise_condicional(value: int) -> int:
    if value < 0:
        raise NotImplementedError("solo este caso")
    return value


def test_cada_tipo_se_dibuja_con_su_campo() -> None:
    params = describe_params(_ejemplo)

    assert [(p.name, p.kind) for p in params] == [
        ("texto", "text"),
        ("cantidad", "int"),
        ("umbral", "float"),
        ("exacto", "bool"),
        ("modo", "choice"),
        ("model", "model"),
    ]
    assert params[0].required
    assert not params[1].required and params[1].default == 3
    assert params[4].choices == ("rápido", "lento")


def test_las_opciones_de_un_literal_mantienen_su_tipo() -> None:
    def con_numeros(cantidad: Literal[1, 2, 3] = 2) -> int:
        return cantidad

    assert describe_params(con_numeros)[0].choices == (1, 2, 3)


def test_un_parametro_sin_tipo_falla_con_mensaje_claro() -> None:
    def sin_tipo(texto) -> str:
        return texto

    with pytest.raises(TypeError, match="le falta el tipo"):
        describe_params(sin_tipo)


def test_detecta_funciones_pendientes() -> None:
    assert is_pending(_pendiente)
    assert not is_pending(_con_raise_condicional)
    assert not is_pending(_ejemplo)


@pytest.mark.parametrize("workshop", all_workshops(), ids=lambda workshop: workshop.role)
def test_cada_taller_se_puede_dibujar(workshop) -> None:
    for tool in workshop.tools:
        describe_params(tool.fn)
    assert workshop.guide is not None and workshop.guide.exists()


def test_arma_una_tabla_markdown_y_escapa_el_pipe() -> None:
    assert markdown_table(("x", "y"), [("a | b", 3)]) == "| x | y |\n|---|---|\n| a \\| b | 3 |"


def test_los_talleres_salen_en_el_orden_de_los_roles() -> None:
    from onboarding.workshop import ROLE_ORDER

    roles = [workshop.role for workshop in all_workshops()]
    assert roles == [role for role in ROLE_ORDER if role in roles]
    assert len(roles) == len(set(roles))


@pytest.mark.parametrize("workshop", all_workshops(), ids=lambda workshop: workshop.role)
def test_cada_pagina_embebida_existe_en_la_app(workshop) -> None:
    from starlette.routing import Match

    from onboarding.api.main import app

    for embed in workshop.embeds:
        scope = {"type": "http", "path": embed.path, "method": "GET", "root_path": ""}
        assert any(route.matches(scope)[0] == Match.FULL for route in app.router.routes), (
            f"{workshop.role}: {embed.path} no es una ruta de la app"
        )


def test_la_conversacion_del_chat_no_se_dibuja_como_campo() -> None:
    def con_historia(pregunta: str, history: ChatHistory = ()) -> str:
        return pregunta

    assert [(p.name, p.kind) for p in describe_params(con_historia)] == [
        ("pregunta", "text"),
        ("history", "history"),
    ]
