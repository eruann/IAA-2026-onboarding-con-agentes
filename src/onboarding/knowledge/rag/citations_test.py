"""Guardrail anti-alucinación: si la cita no está en el corpus, no vale."""

from onboarding.knowledge.rag.citations import quote_is_supported


def test_cita_textual_del_corpus_es_valida(sample_corpus: dict[str, str]) -> None:
    quote = "Toda compra se pide por el formulario interno"

    assert quote_is_supported(quote, sample_corpus["compras.md"])


def test_cita_inventada_no_es_valida(sample_corpus: dict[str, str]) -> None:
    quote = "Las compras las aprueba el gerente general en persona"

    assert not quote_is_supported(quote, sample_corpus["compras.md"])


def test_diferencias_de_acento_y_espacios_no_invalidan_la_cita(
    sample_corpus: dict[str, str],
) -> None:
    quote = "la  aprueba el jefe de area"

    assert quote_is_supported(quote, sample_corpus["compras.md"])


def test_cita_demasiado_corta_se_rechaza(sample_corpus: dict[str, str]) -> None:
    # "compra" aparece en el texto, pero citar una palabra no prueba nada.
    assert not quote_is_supported("compra", sample_corpus["compras.md"])
