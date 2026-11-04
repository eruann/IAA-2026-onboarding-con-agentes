from types import SimpleNamespace

import pytest

from onboarding.agents.answer_question import checks
from onboarding.agents.answer_question.checks import chunk_document, evaluate_retrieval

QUESTIONS = """
- id: compras-001
  question: ¿Cómo pido una compra?
  expected_document: compras.md
  expected_section: Pedido de compra
- id: doble-001
  question: ¿Qué hago con un reclamo?
  expected_document: [incidentes-y-reclamos.md, logistica.md]
  expected_section: null
- id: tesoreria-001
  question: ¿Quién firma los cheques?
  expected_document: tesoreria.md
  expected_section: Firmas
- id: organigrama-001
  question: ¿Quién es el Jefe de Compras?
  expected_document: organigrama.md
  expected_section: Compras
- id: sin-respuesta-001
  question: ¿Cuánto gana un analista?
  expected_document: null
"""

# Lo que "trae" la búsqueda simulada para cada pregunta: lista de (documento, sección)
FOUND = {
    "¿Cómo pido una compra?": [
        ("compras.md", "Pedido de compra"),
        ("proveedores.md", "Pago a proveedores"),
    ],
    "¿Qué hago con un reclamo?": [("logistica.md", "Reclamos"), ("logistica.md", "Reclamos")],
    "¿Quién firma los cheques?": [("organigrama.md", "Finanzas")],
    # Documento correcto, pero no la sección: el jefe de Compras está en otra
    # sección del organigrama que la que trae la búsqueda simulada.
    "¿Quién es el Jefe de Compras?": [("organigrama.md", "Finanzas")],
    "¿Cuánto gana un analista?": [("rrhh-politicas.md", "Sueldos")],
}


@pytest.fixture
def questions(tmp_path, monkeypatch):
    path = tmp_path / "rag_questions.yaml"
    path.write_text(QUESTIONS, encoding="utf-8")
    monkeypatch.setattr(checks, "QUESTIONS_FILE", path)

    def fake_retrieve(query: str, k: int = 5) -> list[SimpleNamespace]:
        return [
            SimpleNamespace(document=document, section=section)
            for document, section in FOUND[query]
        ][:k]

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

    # 3 de 4 preguntas con respuesta traen el documento correcto
    # (compras ✅, reclamo ✅, cheques ❌, organigrama ✅)
    assert "Recall@5: 3/4 (75%)" in report
    # precisión: compras 1/2, reclamo 2/2, cheques 0/1, organigrama 1/1 → promedio
    # 62,5%, que el formato ":.0%" redondea a 62 (banker's rounding de Python)
    assert "Precisión@5: 62%" in report
    assert (
        "| compras-001 | ¿Cómo pido una compra? | compras.md | compras.md, proveedores.md "
        "| ✅ | ✅ |" in report
    )
    assert "| tesoreria-001 |" in report
    assert "| organigrama-001 |" in report
    assert "| sin-respuesta-001 |" in report and "sin respuesta en el corpus" in report


@pytest.mark.usefixtures("questions")
def test_mide_la_seccion_solo_cuando_hay_una_esperada() -> None:
    report = evaluate_retrieval(k=5)

    # doble-001 no tiene una única sección esperada (dos documentos válidos): no
    # cuenta para Sección@k. De las 3 preguntas que sí tienen, solo compras-001
    # trae documento Y sección correctos.
    assert "Sección@5: 1/3 (33%)" in report
    assert "| compras-001 |" in report and report.split("| compras-001 |")[1].startswith(
        " ¿Cómo pido una compra? | compras.md | compras.md, proveedores.md | ✅ | ✅ |"
    )
    doble_row = next(line for line in report.splitlines() if line.startswith("| doble-001 |"))
    assert doble_row.rstrip().endswith("| — |")
    # organigrama-001: trajo el documento correcto pero no la sección
    organigrama_row = next(
        line for line in report.splitlines() if line.startswith("| organigrama-001 |")
    )
    assert organigrama_row.rstrip().endswith("| ✅ | ❌ |")


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
    monkeypatch.setitem(FOUND, "¿Uso A | B?", [("compras.md", "Pedido de compra")])

    row = next(line for line in evaluate_retrieval().splitlines() if "pipe-001" in line)

    assert row == "| pipe-001 | ¿Uso A \\| B? | compras.md | compras.md | ✅ | — |"
