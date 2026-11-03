import pytest
from sqlalchemy import select
from sqlalchemy.orm import Session

from onboarding.db.session import session_scope
from onboarding.game.models import Person


def test_si_te_pasan_una_sesion_usa_esa() -> None:
    given = object()

    with session_scope(given) as session:
        assert session is given


@pytest.mark.db
def test_una_sesion_propia_con_commit_deshace_todo_si_hay_un_error() -> None:
    key = "session-scope-test"
    with pytest.raises(RuntimeError), session_scope(commit=True) as session:
        session.add(Person(key=key, name="No queda", role="X", area="X", is_newcomer=False))
        session.flush()
        raise RuntimeError("algo falló")

    with session_scope() as session:
        assert session.scalar(select(Person).where(Person.key == key)) is None


@pytest.mark.db
def test_una_sesion_propia_sin_commit_no_guarda_nada(db_session: Session) -> None:
    key = "session-scope-sin-commit"
    with session_scope() as session:
        session.add(Person(key=key, name="No queda", role="X", area="X", is_newcomer=False))
        session.flush()

    with session_scope() as session:
        assert session.scalar(select(Person).where(Person.key == key)) is None
