from onboarding.knowledge.rag.corpus import read_documents


def test_devuelve_cada_documento_con_su_nombre() -> None:
    text = read_documents(("organigrama.md", "tesoreria.md"))

    assert '<documento nombre="organigrama.md">' in text
    assert '<documento nombre="tesoreria.md">' in text
    assert "# Organigrama" in text
