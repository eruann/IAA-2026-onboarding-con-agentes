import pytest

from onboarding import paths
from onboarding.agents.generate_quest.checks import review_proposal

QUEST = (
    "key: {key}\ntitle: Misión {key}\ndescription: Algo\npoints: 30\n"
    "approver: manager\nevidence_required: Una prueba\n"
)


def _item(key: str) -> str:
    """Una misión como elemento de una lista YAML."""
    return "- " + QUEST.format(key=key).rstrip("\n").replace("\n", "\n  ") + "\n"


@pytest.fixture(autouse=True)
def existing(tmp_path, monkeypatch):
    # Las misiones que ya existen en el juego
    (tmp_path / "quests.yaml").write_text(_item("ya-existe"), encoding="utf-8")
    monkeypatch.setattr(paths, "DATA_DIR", tmp_path)


def test_una_mision_bien_armada_queda_lista() -> None:
    report = review_proposal(QUEST.format(key="nueva"))

    assert report.startswith("✅ Lista para que la revisen Experiencia y PM.")
    assert "| nueva | Misión nueva | 30 | manager | ✅ |" in report


def test_lee_el_bloque_yaml_aunque_venga_con_texto_alrededor() -> None:
    proposal = "Te propongo esta:\n\n```yaml\n" + QUEST.format(key="nueva") + "```\n¿Te sirve?"

    assert "| nueva |" in review_proposal(proposal)


def test_marca_la_key_que_ya_existe_y_los_campos_que_faltan() -> None:
    proposal = _item("ya-existe") + "- key: corta\n"

    report = review_proposal(proposal)

    assert report.startswith("**2** de 2 con algo para corregir.")
    assert "key repetida" in report and "falta title" in report


def test_avisa_si_no_tiene_el_formato_de_las_misiones() -> None:
    with pytest.raises(ValueError, match="formato de data/quests.yaml"):
        review_proposal("Almorzá con alguien de Logística")
    with pytest.raises(ValueError, match="No es YAML válido"):
        review_proposal("key: [sin cerrar")
