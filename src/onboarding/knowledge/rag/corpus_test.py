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
