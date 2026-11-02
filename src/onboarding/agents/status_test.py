from onboarding.agents import is_pending
from onboarding.knowledge import chunk_text, retrieve


def _pendiente() -> None:
    """Docstring antes del raise: sigue contando como pendiente."""
    raise NotImplementedError("TODO(rol): algo")


def _con_raise_condicional(value: int) -> int:
    if value < 0:
        raise NotImplementedError("solo este caso")
    return value


def test_detecta_una_funcion_sin_implementar() -> None:
    assert is_pending(_pendiente)


def test_un_raise_dentro_de_un_if_no_la_hace_pendiente() -> None:
    assert not is_pending(_con_raise_condicional)


def test_funciones_reales_del_proyecto() -> None:
    assert not is_pending(chunk_text)
    # Si alguien implementa retrieve, este test le avisa que actualice la ficha.
    assert is_pending(retrieve)
