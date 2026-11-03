# producto
# Este archivo es parte del producto: el asistente de onboarding que se
# entrega y se evalúa.

from collections.abc import Iterator
from contextlib import contextmanager
from functools import lru_cache

from sqlalchemy import Engine, create_engine
from sqlalchemy.orm import Session, sessionmaker

from onboarding.config import get_settings


@lru_cache
def get_engine() -> Engine:
    return create_engine(get_settings().database_url, pool_pre_ping=True)


def get_session() -> Iterator[Session]:
    """Dependencia de FastAPI: una sesión por request."""
    session = sessionmaker(bind=get_engine(), expire_on_commit=False)()
    try:
        yield session
    finally:
        session.close()


@contextmanager
def session_scope(session: Session | None = None, commit: bool = False) -> Iterator[Session]:
    """La sesión que te pasan (los tests pasan una que se revierte), o una nueva que se
    cierra al salir. Con `commit`, la nueva confirma los cambios si no hubo error."""
    if session is not None:
        yield session
        return
    with Session(get_engine()) as own:
        if commit:
            with own.begin():
                yield own
        else:
            yield own
