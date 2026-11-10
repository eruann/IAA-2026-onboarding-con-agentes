from contextlib import contextmanager

import pytest
from sqlalchemy import func, select
from sqlalchemy.orm import Session

import onboarding.game.rewards as rewards
from onboarding.game.models import Person, QuestAssignment, QuestRow, Redemption

CATALOG = [
    {"key": "coffee", "title": "Café", "cost": 40},
    {"key": "course", "title": "Curso", "cost": 100},
]


def _catalog(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(rewards, "load_data_yaml", lambda name, required=False: CATALOG)


def _person_with_points(session: Session, points: int) -> Person:
    person = Person(key="t-reward-user", name="Ana", role="Analista", area="X")
    quest = QuestRow(
        key="t-reward-quest",
        title="Misión",
        description="Algo",
        points=points,
        approver="manager",
        evidence_required="Una prueba",
    )
    session.add_all([person, quest])
    session.flush()
    session.add(QuestAssignment(person_id=person.id, quest_id=quest.id, status="approved"))
    session.flush()
    return person


def test_lista_el_catalogo_desde_rewards_yaml(monkeypatch: pytest.MonkeyPatch) -> None:
    _catalog(monkeypatch)

    assert rewards.list_rewards() == CATALOG


@pytest.mark.db
def test_canjea_y_devuelve_el_saldo_restante(
    db_session: Session, monkeypatch: pytest.MonkeyPatch
) -> None:
    _catalog(monkeypatch)
    _person_with_points(db_session, 100)

    remaining = rewards.redeem("t-reward-user", "coffee", db_session)

    assert remaining == 60
    redemption = db_session.scalar(select(Redemption))
    assert (redemption.reward_key, redemption.points_spent) == ("coffee", 40)


@pytest.mark.db
def test_rechaza_saldo_insuficiente_sin_guardar_el_canje(
    db_session: Session, monkeypatch: pytest.MonkeyPatch
) -> None:
    _catalog(monkeypatch)
    _person_with_points(db_session, 50)

    with pytest.raises(ValueError, match="Puntos insuficientes"):
        rewards.redeem("t-reward-user", "course", db_session)

    assert db_session.scalar(select(func.count()).select_from(Redemption)) == 0


@pytest.mark.db
def test_canjear_dos_veces_no_permite_gastar_el_mismo_saldo(
    db_session: Session, monkeypatch: pytest.MonkeyPatch
) -> None:
    _catalog(monkeypatch)
    _person_with_points(db_session, 50)

    assert rewards.redeem("t-reward-user", "coffee", db_session) == 10
    with pytest.raises(ValueError, match="Puntos insuficientes"):
        rewards.redeem("t-reward-user", "coffee", db_session)

    assert db_session.scalar(select(func.count()).select_from(Redemption)) == 1


@pytest.mark.db
def test_historial_muestra_canjes_mas_nuevos_primero(
    db_session: Session, monkeypatch: pytest.MonkeyPatch
) -> None:
    _catalog(monkeypatch)
    person = _person_with_points(db_session, 100)
    db_session.add_all(
        [
            Redemption(
                person_id=person.id,
                reward_key="coffee",
                points_spent=40,
            ),
            Redemption(
                person_id=person.id,
                reward_key="course",
                points_spent=100,
            ),
        ]
    )
    db_session.flush()

    @contextmanager
    def use_test_session(session=None, commit=False):
        yield db_session

    monkeypatch.setattr(rewards, "session_scope", use_test_session)

    history = rewards.redemption_history("t-reward-user")

    assert [item["reward_key"] for item in history] == ["course", "coffee"]
    assert [item["title"] for item in history] == ["Curso", "Café"]
    assert [item["points_spent"] for item in history] == [100, 40]


@pytest.mark.db
def test_persona_inexistente_no_puede_canjear(
    db_session: Session, monkeypatch: pytest.MonkeyPatch
) -> None:
    _catalog(monkeypatch)

    with pytest.raises(ValueError, match="No existe la persona"):
        rewards.redeem("no-existe", "coffee", db_session)


def test_premio_inexistente_no_puede_canjear(monkeypatch: pytest.MonkeyPatch) -> None:
    _catalog(monkeypatch)

    with pytest.raises(ValueError, match="No existe el premio"):
        rewards.redeem("t-reward-user", "unknown")
