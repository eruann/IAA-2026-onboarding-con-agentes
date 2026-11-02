from typing import Literal

import pytest
from langchain_core.language_models import BaseChatModel

from onboarding.workshop import all_workshops, describe_params, is_pending


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
