from pathlib import Path

import pytest

from onboarding import paths
from onboarding.game.quests import (
    QUEST_FIELDS,
    check_quests,
    field_problems,
    is_positive_int,
    quests_in_data,
)

QUEST = {
    "key": "a",
    "title": "Misión a",
    "description": "Algo",
    "points": 10,
    "approver": "manager",
    "evidence_required": "Una prueba",
}


def test_una_mision_bien_armada_no_tiene_problemas() -> None:
    assert check_quests([QUEST]) == [[]]


def test_marca_campos_puntos_aprobador_y_keys_repetidas() -> None:
    bad = {**QUEST, "points": 0, "approver": "jefe", "extra": 1}
    del bad["title"]

    problems = check_quests([bad], existing_keys={"a"})[0]

    assert "falta title" in problems
    assert "extra no se usa" in problems
    assert "key repetida" in problems
    assert "points tiene que ser un entero mayor que cero" in problems
    assert "approver tiene que ser manager, helpdesk, agent" in problems


def test_las_ayudas_de_las_reglas() -> None:
    seen: set = set()
    assert field_problems({"key": "x"}, ("key",), seen) == []
    assert field_problems({"key": "x"}, ("key",), seen) == ["key repetida"]
    assert is_positive_int(3) and not is_positive_int(0) and not is_positive_int(True)
    assert QUEST_FIELDS == tuple(QUEST)


def test_lee_las_misiones_de_data(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setattr(paths, "DATA_DIR", tmp_path)
    with pytest.raises(FileNotFoundError, match="quests.yaml"):
        quests_in_data()
    (tmp_path / "quests.yaml").write_text("- key: a\n", encoding="utf-8")
    assert quests_in_data() == [{"key": "a"}]
