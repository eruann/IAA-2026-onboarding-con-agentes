from collections.abc import Iterator

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from onboarding.api.main import create_app
from onboarding.db.session import get_session
from onboarding.game.models import Person, QuestAssignment, QuestRow


class _ResultadoVacio:
    def all(self) -> list:
        return []


class _SesionVacia:
    """Sesión falsa sin datos: el panel se puede probar sin Postgres."""

    def scalars(self, _statement: object) -> _ResultadoVacio:
        return _ResultadoVacio()

    def execute(self, _statement: object) -> _ResultadoVacio:
        return _ResultadoVacio()


def _cliente_con_sesion(session: object) -> Iterator[TestClient]:
    app: FastAPI = create_app()
    app.dependency_overrides[get_session] = lambda: session
    try:
        yield TestClient(app)
    finally:
        app.dependency_overrides.clear()


@pytest.fixture
def cliente_sin_datos() -> Iterator[TestClient]:
    yield from _cliente_con_sesion(_SesionVacia())


@pytest.fixture
def cliente_con_base(db_session: Session) -> Iterator[TestClient]:
    yield from _cliente_con_sesion(db_session)


def test_panel_sin_datos_renderiza_los_mensajes_vacios(cliente_sin_datos: TestClient) -> None:
    response = cliente_sin_datos.get("/panel")

    assert response.status_code == 200
    assert "Panel del jefe" in response.text
    assert "Nada pendiente." in response.text
    assert "Todavía no hay datos" in response.text


def _quest(key: str, title: str) -> QuestRow:
    return QuestRow(
        key=key,
        title=title,
        description="Descripción",
        points=10,
        approver="manager",
        evidence_required="Confirmación",
    )


@pytest.mark.db
def test_panel_muestra_primero_lo_que_espera_aprobacion(
    db_session: Session, cliente_con_base: TestClient
) -> None:
    person = Person(
        key="panel-test-ingresante",
        name="Ingresante de prueba",
        role="Analista",
        area="Operaciones",
        is_newcomer=True,
    )
    # "Armar" va antes que "Conocer" por título: si el panel ordenara solo por
    # título, la pendiente quedaría primero.
    pendiente = _quest("panel-test-pendiente", "Armar el escritorio")
    entregada = _quest("panel-test-entregada", "Conocer el equipo")
    aprobada = _quest("panel-test-aprobada", "Firmar el contrato")
    db_session.add_all([person, pendiente, entregada, aprobada])
    db_session.flush()
    db_session.add_all(
        [
            QuestAssignment(person_id=person.id, quest_id=pendiente.id, status="pending"),
            QuestAssignment(person_id=person.id, quest_id=entregada.id, status="submitted"),
            QuestAssignment(person_id=person.id, quest_id=aprobada.id, status="approved"),
        ]
    )
    db_session.flush()

    response = cliente_con_base.get("/panel")

    assert response.status_code == 200
    html = response.text
    assert "Ingresante de prueba — Analista, Operaciones" in html
    assert "<td>Esperando aprobación</td>" in html
    assert "<td>Pendiente</td>" in html
    assert html.index("Conocer el equipo") < html.index("Armar el escritorio")
    # Lo aprobado ya no necesita nada del jefe.
    assert "Firmar el contrato" not in html
