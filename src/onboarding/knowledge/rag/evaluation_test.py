import pytest

from onboarding.knowledge.rag import evaluation
from onboarding.knowledge.rag.retriever import RetrievedChunk


def _retrieve_fijo(document: str):
    def retrieve(query: str, k: int = 5) -> list[RetrievedChunk]:
        return [RetrievedChunk(text="...", document=document, section="", score=1.0)]

    return retrieve


def test_marca_acierto_cuando_trae_el_documento_esperado(
    tmp_path, monkeypatch: pytest.MonkeyPatch
) -> None:
    questions = tmp_path / "rag_questions.yaml"
    questions.write_text(
        "- id: compras-001\n"
        "  question: ¿Cómo pido una compra?\n"
        "  expected_document: compras.md\n"
        "- id: sin-respuesta-001\n"
        "  question: ¿Cuánto gana un analista?\n"
        "  expected_document: null\n",
        encoding="utf-8",
    )
    monkeypatch.setattr(evaluation, "QUESTIONS", questions)
    monkeypatch.setattr(evaluation, "retrieve", _retrieve_fijo("compras.md"))

    rows = evaluation.evaluate_retrieval()

    assert [row["id"] for row in rows] == ["compras-001"]
    assert rows[0]["acierto"] is True


def test_acepta_cualquiera_de_los_documentos_esperados(
    tmp_path, monkeypatch: pytest.MonkeyPatch
) -> None:
    questions = tmp_path / "rag_questions.yaml"
    questions.write_text(
        "- id: incidentes-001\n"
        "  question: ¿A quién reporto un reclamo?\n"
        "  expected_document: [incidentes-y-reclamos.md, logistica.md]\n",
        encoding="utf-8",
    )
    monkeypatch.setattr(evaluation, "QUESTIONS", questions)
    monkeypatch.setattr(evaluation, "retrieve", _retrieve_fijo("logistica.md"))

    assert evaluation.evaluate_retrieval()[0]["acierto"] is True


def test_el_set_real_existe_y_se_puede_leer() -> None:
    assert evaluation.QUESTIONS.exists()
