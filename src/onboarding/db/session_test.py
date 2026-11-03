from collections.abc import Iterator

import pytest
from sqlalchemy import delete, select

from onboarding.db.session import session_scope
from onboarding.game.models import Person

# Estos tests abren sesiones propias contra la base real: cada uno borra al final
# lo que pudo haber quedado, aunque el código ande mal.
KEY = "session-scope-test"


@pytest.fixture
def cleanup() -> Iterator[None]:
    yield
    with session_scope(commit=True) as session:
        session.execute(delete(Person).where(Person.key == KEY))


def _person() -> Person:
    return Person(key=KEY, name="Prueba", role="X", area="X", is_newcomer=False)


def _saved() -> Person | None:
    with session_scope() as session:
        return session.scalar(select(Person).where(Person.key == KEY))


def test_si_te_pasan_una_sesion_usa_esa() -> None:
    given = object()

    with session_scope(given) as session:
        assert session is given


@pytest.mark.db
def test_una_sesion_propia_con_commit_guarda_al_salir(cleanup) -> None:
    with session_scope(commit=True) as session:
        session.add(_person())

    assert _saved() is not None


@pytest.mark.db
def test_una_sesion_propia_con_commit_deshace_todo_si_hay_un_error(cleanup) -> None:
    with pytest.raises(RuntimeError), session_scope(commit=True) as session:
        session.add(_person())
        session.flush()
        raise RuntimeError("algo falló")

    assert _saved() is None


@pytest.mark.db
def test_una_sesion_propia_sin_commit_no_guarda_nada(cleanup) -> None:
    with session_scope() as session:
        session.add(_person())
        session.flush()

    assert _saved() is None
