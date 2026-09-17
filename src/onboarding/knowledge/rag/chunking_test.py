import pytest

from onboarding.knowledge.rag.chunking import chunk_text


def test_documento_corto_queda_en_un_solo_fragmento(sample_corpus: dict[str, str]) -> None:
    chunks = chunk_text(sample_corpus["mesa-de-ayuda.md"])

    assert len(chunks) == 1


def test_documento_largo_se_parte_respetando_el_maximo() -> None:
    text = "\n\n".join(f"Párrafo número {i}. " * 10 for i in range(20))

    chunks = chunk_text(text, max_chars=300, overlap=0)

    assert len(chunks) > 1
    assert all(len(chunk) <= 300 for chunk in chunks)


def test_parrafo_mas_largo_que_el_maximo_se_corta_igual() -> None:
    chunks = chunk_text("x" * 1000, max_chars=100, overlap=0)

    assert len(chunks) == 10


def test_overlap_mayor_o_igual_al_maximo_es_error() -> None:
    with pytest.raises(ValueError):
        chunk_text("texto", max_chars=100, overlap=100)
