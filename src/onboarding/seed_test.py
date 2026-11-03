import pytest
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from onboarding.game.models import Person, QuestAssignment, QuestRow
from onboarding.seed import seed

QUESTS_YAML = (
    "- key: seed-test-quest\n"
    "  title: Misión de prueba\n"
    "  description: Descripción\n"
    "  points: 10\n"
    "  approver: manager\n"
    "  evidence_required: Confirmación\n"
)


def _people_yaml(name: str) -> str:
    return (
        "- key: seed-test-ingresante\n"
        f"  name: {name}\n"
        "  role: Analista\n"
        "  area: Pruebas\n"
        "  is_newcomer: true\n"
    )


@pytest.fixture
def data_dir(tmp_path, monkeypatch: pytest.MonkeyPatch):
    (tmp_path / "people.yaml").write_text(_people_yaml("Ingresante seed test"), encoding="utf-8")
    (tmp_path / "quests.yaml").write_text(QUESTS_YAML, encoding="utf-8")
    (tmp_path / "rewards.yaml").write_text("[]\n", encoding="utf-8")
    monkeypatch.setattr("onboarding.paths.DATA_DIR", tmp_path)
    return tmp_path


def _assignments(session: Session, person: Person) -> int:
    return session.scalar(
        select(func.count(QuestAssignment.id)).where(QuestAssignment.person_id == person.id)
    )


@pytest.mark.db
def test_seed_carga_datos_de_juego_sin_duplicar(db_session: Session, data_dir) -> None:
    seed(with_corpus=False, session=db_session)
    seed(with_corpus=False, session=db_session)

    person = db_session.scalar(select(Person).where(Person.key == "seed-test-ingresante"))
    quest = db_session.scalar(select(QuestRow).where(QuestRow.key == "seed-test-quest"))
    assert person is not None
    assert quest is not None
    assert person.name == "Ingresante seed test"
    assert _assignments(db_session, person) == 1


@pytest.mark.db
def test_seed_corrige_el_nombre_sin_crear_otra_persona(db_session: Session, data_dir) -> None:
    seed(with_corpus=False, session=db_session)
    (data_dir / "people.yaml").write_text(_people_yaml("Nombre corregido"), encoding="utf-8")

    seed(with_corpus=False, session=db_session)

    people = db_session.scalars(select(Person).where(Person.key == "seed-test-ingresante")).all()
    assert [person.name for person in people] == ["Nombre corregido"]
    assert _assignments(db_session, people[0]) == 1
