import pytest

from onboarding.game import workshop
from onboarding.game.workshop import review_quests, review_rewards

QUEST = (
    "- key: {key}\n  title: Misión {key}\n  description: Algo\n  points: {points}\n"
    "  approver: {approver}\n  evidence_required: Una prueba\n"
)


@pytest.fixture
def data(tmp_path, monkeypatch):
    monkeypatch.setattr(workshop, "DATA_DIR", tmp_path)
    return tmp_path


def test_las_misiones_bien_armadas_pasan(data) -> None:
    quests = "".join(QUEST.format(key=f"m{i}", points=10, approver="manager") for i in range(6))
    (data / "quests.yaml").write_text(quests, encoding="utf-8")

    report = review_quests()

    assert "✅ 6 misiones" in report
    assert "**0** con algo para revisar · **60** puntos en total." in report


def test_marca_lo_que_no_cierra_en_las_misiones(data) -> None:
    quests = (
        QUEST.format(key="a", points=10, approver="manager")
        + QUEST.format(key="a", points=0, approver="jefe")
        + "- key: b\n  title: Sin el resto\n  extra: 1\n"
    )
    (data / "quests.yaml").write_text(quests, encoding="utf-8")

    report = review_quests()

    assert "⚠️ Hay 3 misiones: el alcance pide de 6 a 8." in report
    assert "key repetida" in report
    assert "points tiene que ser un entero mayor que cero" in report
    assert "approver tiene que ser manager, helpdesk, agent" in report
    assert "falta description" in report and "extra no se usa" in report
    assert "**2** con algo para revisar" in report


def test_compara_cada_premio_con_los_puntos_de_todas_las_misiones(data) -> None:
    quests = QUEST.format(key="a", points=40, approver="agent") + QUEST.format(
        key="b", points=60, approver="agent"
    )
    (data / "quests.yaml").write_text(quests, encoding="utf-8")
    (data / "rewards.yaml").write_text(
        "- key: cafe\n  title: Café\n  cost: 50\n"
        "- key: viaje\n  title: Viaje\n  cost: 500\n"
        "- key: raro\n  title: Raro\n  cost: gratis\n",
        encoding="utf-8",
    )

    report = review_rewards()

    assert "Todas las misiones juntas dan **100** puntos." in report
    assert "| cafe | Café | 50 | 50% | ✅ |" in report
    assert "| viaje | Viaje | 500 | 500% | cuesta más que todas las misiones juntas |" in report
    assert "cost tiene que ser un entero mayor que cero" in report


def test_avisa_si_falta_el_archivo(data) -> None:
    with pytest.raises(FileNotFoundError, match="quests.yaml"):
        review_quests()


def test_las_misiones_reales_se_pueden_revisar() -> None:
    assert "| key | título |" in review_quests()
    assert "| key | premio |" in review_rewards()
