"""Fixtures compartidas. Todo el equipo escribe tests contra estas.

Tres capas, separadas por marker:
  - sin marker            unitaria: sin base, sin red, sin modelo real
  - @pytest.mark.db       integración: Postgres de verdad
  - @pytest.mark.llm      gasta plata; nunca corre en CI

CI corre:  pytest -m "not llm"
"""

import os

import pytest
from fastapi.testclient import TestClient
from langchain_core.language_models import FakeListChatModel
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

# El default de los tests es el proveedor fake: ningún test toca la red ni
# gasta tokens salvo que esté marcado con @pytest.mark.llm.
os.environ.setdefault("LLM_PROVIDER", "fake")
os.environ.setdefault("ENV", "test")

from onboarding.api.main import create_app  # noqa: E402
from onboarding.config import get_settings  # noqa: E402


def _database_available(url: str) -> bool:
    try:
        create_engine(url).connect().close()
    except Exception:
        return False
    return True


@pytest.fixture(scope="session")
def database_url() -> str:
    return get_settings().database_url


@pytest.fixture(autouse=True)
def _skip_db_tests_without_database(request: pytest.FixtureRequest) -> None:
    """Sin Postgres, los tests `db` se saltean en local pero fallan en CI.

    Así nadie queda bloqueado por no tener la base levantada, y al mismo tiempo
    CI no puede quedar verde salteando la mitad de la suite (REQUIRE_DB=1).
    """
    if request.node.get_closest_marker("db") is None:
        return
    if _database_available(get_settings().database_url):
        return
    if os.environ.get("REQUIRE_DB") == "1":
        pytest.fail("No hay Postgres y REQUIRE_DB=1")
    pytest.skip("Postgres no disponible: levantalo con docker compose up")


@pytest.fixture
def db_session(database_url: str) -> Session:
    """Sesión dentro de una transacción que se revierte al terminar el test.

    Cada test queda aislado sin borrar tablas ni recrear la base.
    """
    engine = create_engine(database_url)
    connection = engine.connect()
    transaction = connection.begin()
    session = Session(bind=connection)
    try:
        yield session
    finally:
        session.close()
        transaction.rollback()
        connection.close()


@pytest.fixture
def client() -> TestClient:
    return TestClient(create_app())


@pytest.fixture
def fake_llm() -> FakeListChatModel:
    """Modelo con respuestas programadas: determinístico y gratis."""
    return FakeListChatModel(responses=["respuesta de prueba"])


@pytest.fixture
def sample_corpus() -> dict[str, str]:
    """Dos documentos cortos, suficientes para chunking y verificación de citas."""
    return {
        "compras.md": (
            "# Compras\n\n"
            "## Pedido de compra\n\n"
            "Toda compra se pide por el formulario interno y la aprueba el jefe "
            "de área antes de llegar a Administración.\n\n"
            "## Excepciones\n\n"
            "Las compras de menos de 50 dólares las autoriza el propio equipo."
        ),
        "mesa-de-ayuda.md": (
            "# Mesa de Ayuda\n\n"
            "## Alta de casilla de mail\n\n"
            "La casilla se pide llamando al interno 100 el primer día."
        ),
    }
