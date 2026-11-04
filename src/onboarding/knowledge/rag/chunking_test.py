import pytest

from onboarding.knowledge.rag.chunking import chunk_text


def test_documento_corto_queda_en_un_solo_fragmento(sample_corpus: dict[str, str]) -> None:
    chunks = chunk_text(sample_corpus["mesa-de-ayuda.md"])

    assert len(chunks) == 1
    assert chunks[0].section == "Alta de casilla de mail"


def test_cada_fragmento_sabe_su_seccion(sample_corpus: dict[str, str]) -> None:
    chunks = chunk_text(sample_corpus["compras.md"])

    assert [chunk.section for chunk in chunks] == ["Pedido de compra", "Excepciones"]
    assert "formulario interno" in chunks[0].text
    assert "50 dólares" in chunks[1].text


def test_el_titulo_del_documento_no_genera_un_fragmento_propio() -> None:
    # Antes del primer "##" solo está el "#" del documento: no es contenido.
    text = "# Un documento\n\n## Única sección\n\nTexto de la sección."

    chunks = chunk_text(text)

    assert len(chunks) == 1
    assert chunks[0].section == "Única sección"


def test_texto_antes_del_primer_encabezado_queda_con_seccion_vacia() -> None:
    text = "# Título\n\nIntro sin encabezado propio.\n\n## Sección\n\nCuerpo."

    chunks = chunk_text(text)

    assert chunks[0].section == ""
    assert "Intro sin encabezado propio" in chunks[0].text
    assert chunks[1].section == "Sección"


# recorrido: tests-rag
def test_seccion_larga_se_parte_respetando_el_maximo() -> None:
    body = "\n\n".join(f"Párrafo número {i}. " * 10 for i in range(20))
    text = f"# Título\n\n## Sección\n\n{body}"

    chunks = chunk_text(text, max_chars=300, overlap=0)

    assert len(chunks) > 1
    assert all(chunk.section == "Sección" for chunk in chunks)
    assert all(len(chunk.text) <= 300 for chunk in chunks)


def test_parrafo_mas_largo_que_el_maximo_se_corta_igual() -> None:
    text = f"## Sección\n\n{'x' * 1000}"

    chunks = chunk_text(text, max_chars=100, overlap=0)

    assert len(chunks) == 10
    assert all(chunk.section == "Sección" for chunk in chunks)


def test_overlap_mayor_o_igual_al_maximo_es_error() -> None:
    with pytest.raises(ValueError):
        chunk_text("texto", max_chars=100, overlap=100)
