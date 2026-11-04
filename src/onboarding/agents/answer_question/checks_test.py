from types import SimpleNamespace

import pytest

from onboarding.agents.answer_question import checks
from onboarding.agents.answer_question.checks import chunk_document, evaluate_retrieval

QUESTIONS = """
- id: compras-001
  question: ¿Cómo pido una compra?
  expected_document: compras.md
- id: doble-001
  question: ¿Qué hago con un reclamo?
  expected_document: [incidentes-y-reclamos.md, logistica.md]
- id: tesoreria-001
  question: ¿Quién firma los cheques?
  expected_document: tesoreria.md
- id: sin-respuesta-001
  question: ¿Cuánto gana un analista?
  expected_document: null
"""

# Lo que "trae" la búsqueda simulada para cada pregunta
FOUND = {
    "¿Cómo pido una compra?": ["compras.md", "proveedores.md"],
    "¿Qué hago con un reclamo?": ["logistica.md", "logistica.md"],
    "¿Quién firma los cheques?": ["organigrama.md"],
    "¿Cuánto gana un analista?": ["rrhh-politicas.md"],
}


@pytest.fixture
def questions(tmp_path, monkeypatch):
    path = tmp_path / "rag_questions.yaml"
    path.write_text(QUESTIONS, encoding="utf-8")
    monkeypatch.setattr(checks, "QUESTIONS_FILE", path)

    def fake_retrieve(query: str, k: int = 5) -> list[SimpleNamespace]:
        return [SimpleNamespace(document=doc) for doc in FOUND[query]][:k]

    monkeypatch.setattr(checks, "retrieve", fake_retrieve)


def test_cada_fragmento_dice_su_largo_y_su_seccion() -> None:
    rows = chunk_document("tesoreria.md", max_chars=1200, overlap=0)

    assert len(rows) > 1
    assert [row["fragmento"] for row in rows] == list(range(1, len(rows) + 1))
    assert all(row["caracteres"] == len(row["texto"]) for row in rows)
    assert all(row["sección"] for row in rows)


@pytest.mark.usefixtures("questions")
def test_mide_recall_y_precision_sin_contar_las_preguntas_sin_respuesta() -> None:
    report = evaluate_retrieval(k=5)

    # 2 de 3 preguntas con respuesta traen el documento correcto
    assert "Recall@5: 2/3 (67%)" in report
    # precisión: compras 1/2, reclamo 2/2, cheques 0/1 → promedio 50%
    assert "Precisión@5: 50%" in report
    assert (
        "| compras-001 | ¿Cómo pido una compra? | compras.md | compras.md, proveedores.md | ✅ |"
        in report
    )
    assert "| tesoreria-001 |" in report and "| ❌ |" in report
    assert "| sin-respuesta-001 |" in report and "sin respuesta en el corpus" in report


def test_avisa_si_no_esta_el_set_de_preguntas(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(checks, "QUESTIONS_FILE", tmp_path / "no-existe.yaml")

    with pytest.raises(FileNotFoundError, match="imagen de desarrollo"):
        evaluate_retrieval()


@pytest.mark.usefixtures("questions")
def test_un_pipe_en_la_pregunta_no_rompe_la_tabla(monkeypatch) -> None:
    path = checks.QUESTIONS_FILE
    path.write_text(
        "- id: pipe-001\n  question: ¿Uso A | B?\n  expected_document: compras.md\n",
        encoding="utf-8",
    )
    monkeypatch.setitem(FOUND, "¿Uso A | B?", ["compras.md"])

    row = next(line for line in evaluate_retrieval().splitlines() if "pipe-001" in line)

    assert row == "| pipe-001 | ¿Uso A \\| B? | compras.md | compras.md | ✅ |"
