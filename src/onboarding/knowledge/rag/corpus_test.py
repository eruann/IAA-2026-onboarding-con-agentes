from pathlib import Path

import pytest

from onboarding.knowledge.rag.corpus import document_names, read_documents


def test_devuelve_cada_documento_con_su_nombre() -> None:
    text = read_documents(("organigrama.md", "tesoreria.md"))

    assert '<documento nombre="organigrama.md">' in text
    assert '<documento nombre="tesoreria.md">' in text
    assert "# Organigrama" in text


def test_lista_los_documentos_del_corpus_sin_el_readme() -> None:
    names = document_names()

    assert "tesoreria.md" in names and "organigrama.md" in names
    assert "README.md" not in names
    assert list(names) == sorted(names)


def test_un_documento_en_una_subcarpeta_se_lista_y_se_lee_con_su_ruta(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    (tmp_path / "compras").mkdir()
    (tmp_path / "compras" / "pedidos.md").write_text("# Pedidos", encoding="utf-8")
    (tmp_path / "compras" / "README.md").write_text("la carpeta", encoding="utf-8")
    monkeypatch.setattr("onboarding.knowledge.rag.corpus.CORPUS_DIR", tmp_path)

    assert document_names() == ("compras/pedidos.md",)
    assert "# Pedidos" in read_documents(document_names())
