import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from onboarding.api.main import create_app
from onboarding.db.session import get_session
from onboarding.game.models import Person, QuestAssignment, QuestRow


@pytest.mark.db
def test_panel_muestra_ingresantes_y_misiones_pendientes(db_session: Session) -> None:
    person = Person(
        name="Ingresante de prueba",
        role="Analista",
        area="Operaciones",
        is_newcomer=True,
    )
    quest = QuestRow(
        key="panel-test-quest",
        title="Conocer el equipo",
        description="Presentarse al equipo",
        points=10,
        approver="manager",
        evidence_required="Confirmación",
    )
    db_session.add_all([person, quest])
    db_session.flush()
    db_session.add(QuestAssignment(person_id=person.id, quest_id=quest.id, status="pending"))
    db_session.flush()

    app = create_app()
    app.dependency_overrides[get_session] = lambda: db_session
    try:
        response = TestClient(app).get("/panel")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert "Ingresante de prueba" in response.text
    assert "Analista" in response.text
    assert "Conocer el equipo" in response.text
    assert "Pendiente" in response.text
    assert "Aprobar" not in response.text
