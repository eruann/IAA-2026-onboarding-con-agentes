import pytest
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from onboarding.game.models import Person, QuestAssignment, QuestRow
from onboarding.seed import seed


@pytest.mark.db
def test_seed_carga_datos_de_juego_sin_duplicar(
    db_session: Session, tmp_path, monkeypatch: pytest.MonkeyPatch
) -> None:
    (tmp_path / "people.yaml").write_text(
        "- name: Ingresante seed test\n  role: Analista\n  area: Pruebas\n  is_newcomer: true\n",
        encoding="utf-8",
    )
    (tmp_path / "quests.yaml").write_text(
        "- key: seed-test-quest\n"
        "  title: Misión de prueba\n"
        "  description: Descripción\n"
        "  points: 10\n"
        "  approver: manager\n"
        "  evidence_required: Confirmación\n",
        encoding="utf-8",
    )
    (tmp_path / "rewards.yaml").write_text("[]\n", encoding="utf-8")
    monkeypatch.setattr("onboarding.seed.DATA_DIR", tmp_path)

    seed(with_corpus=False, session=db_session)
    seed(with_corpus=False, session=db_session)

    person = db_session.scalar(select(Person).where(Person.name == "Ingresante seed test"))
    quest = db_session.scalar(select(QuestRow).where(QuestRow.key == "seed-test-quest"))
    assert person is not None
    assert quest is not None
    assert (
        db_session.scalar(
            select(func.count(QuestAssignment.id)).where(
                QuestAssignment.person_id == person.id,
                QuestAssignment.quest_id == quest.id,
            )
        )
        == 1
    )
