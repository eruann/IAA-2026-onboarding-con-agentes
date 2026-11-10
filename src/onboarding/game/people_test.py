from pathlib import Path

import pytest
import yaml
from sqlalchemy.orm import Session

from onboarding.game.models import Person
from onboarding.game.people import list_people, person_card, team_for_manager

MANAGER_DATA = [
    {
        "key": "t-manager-a",
        "name": "Jefa A",
        "role": "Jefa",
        "area": "X",
        "is_newcomer": False,
        "is_manager": True,
    },
    {
        "key": "t-manager-empty",
        "name": "Jefe sin equipo",
        "role": "Jefe",
        "area": "X",
        "is_newcomer": False,
        "is_manager": True,
    },
    {
        "key": "t-not-manager",
        "name": "Ingresante",
        "role": "Analista",
        "area": "X",
        "is_newcomer": True,
        "is_manager": False,
    },
    {
        "key": "t-new-a1",
        "name": "Ingresante A1",
        "role": "Analista",
        "area": "X",
        "is_newcomer": True,
        "manager_key": "t-manager-a",
    },
    {
        "key": "t-new-a2",
        "name": "Ingresante A2",
        "role": "Analista",
        "area": "X",
        "is_newcomer": True,
        "manager_key": "t-manager-a",
    },
    {
        "key": "t-new-unmanaged",
        "name": "Ingresante sin jefe válido",
        "role": "Analista",
        "area": "X",
        "is_newcomer": True,
        "manager_key": "t-not-manager",
    },
]


def _use_people_yaml(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, people: list[dict]) -> None:
    (tmp_path / "people.yaml").write_text(
        yaml.safe_dump(people, allow_unicode=True), encoding="utf-8"
    )
    monkeypatch.setattr("onboarding.paths.DATA_DIR", tmp_path)


def _person_rows(people: list[dict]) -> list[Person]:
    return [
        Person(
            key=person["key"],
            name=person["name"],
            role=person["role"],
            area=person["area"],
            is_newcomer=person["is_newcomer"],
        )
        for person in people
    ]


@pytest.mark.db
def test_lista_primero_a_los_ingresantes(db_session: Session) -> None:
    db_session.add_all(
        [
            Person(key="t-jefa", name="AAA Jefa", role="Jefa", area="X", is_newcomer=False),
            Person(key="t-nuevo", name="ZZZ Nuevo", role="Analista", area="X", is_newcomer=True),
        ]
    )
    db_session.flush()

    keys = [card.key for card in list_people(db_session)]

    assert keys.index("t-nuevo") < keys.index("t-jefa")
    nuevo = next(card for card in list_people(db_session) if card.key == "t-nuevo")
    assert (nuevo.name, nuevo.role, nuevo.is_newcomer) == ("ZZZ Nuevo", "Analista", True)


def test_la_tarjeta_de_una_persona_tiene_lo_que_muestra_la_interfaz() -> None:
    person = Person(key="k", name="Ana", role="Analista", area="Operaciones", is_newcomer=True)

    assert person_card(person).name == "Ana" and person_card(person).is_newcomer


@pytest.mark.db
def test_devuelve_los_ingresantes_del_jefe(
    db_session: Session, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _use_people_yaml(tmp_path, monkeypatch, MANAGER_DATA)
    db_session.add_all(_person_rows(MANAGER_DATA))
    db_session.flush()

    team = team_for_manager("t-manager-a", db_session)

    assert [person.key for person in team] == ["t-new-a1", "t-new-a2"]


@pytest.mark.db
def test_jefe_sin_equipo_devuelve_lista_vacia(
    db_session: Session, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _use_people_yaml(tmp_path, monkeypatch, MANAGER_DATA)
    db_session.add_all(_person_rows(MANAGER_DATA))
    db_session.flush()

    assert team_for_manager("t-manager-empty", db_session) == []


@pytest.mark.db
@pytest.mark.parametrize("manager_key", ["no-existe", "t-not-manager"])
def test_clave_inexistente_o_de_no_jefe_devuelve_lista_vacia(
    db_session: Session,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    manager_key: str,
) -> None:
    _use_people_yaml(tmp_path, monkeypatch, MANAGER_DATA)
    db_session.add_all(_person_rows(MANAGER_DATA))
    db_session.flush()

    assert team_for_manager(manager_key, db_session) == []
