from typing import Literal

import pytest
from langchain_core.language_models import BaseChatModel

from onboarding.agents import BY_KEY
from onboarding.workshop import all_workshops, describe_params


def _ejemplo(
    texto: str,
    cantidad: int = 3,
    umbral: float = 0.5,
    exacto: bool = False,
    modo: Literal["rápido", "lento"] = "rápido",
    model: BaseChatModel | None = None,
) -> str:
    return texto


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


def test_las_keys_de_los_talleres_no_se_repiten() -> None:
    keys = [workshop.key for workshop in all_workshops()]

    assert len(keys) == len(set(keys))


@pytest.mark.parametrize("workshop", all_workshops(), ids=lambda workshop: workshop.key)
def test_cada_taller_es_dibujable(workshop) -> None:
    # El agente existe en el registro y cada prueba tiene tipos que la UI sabe dibujar
    assert workshop.agent is None or workshop.agent in BY_KEY
    for tool in workshop.tools:
        describe_params(tool.fn)
    assert workshop.guide is not None and workshop.guide.exists()
