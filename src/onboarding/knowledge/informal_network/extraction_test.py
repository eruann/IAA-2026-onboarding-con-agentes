"""La extracción se prueba con un modelo de salida fija: sin red y determinístico.

Lo que se testea acá es lo que hace el código alrededor del modelo (el filtro de
evidencia y el contexto que recibe), no la calidad de la extracción. Eso se mide
en eval/.
"""

import pytest
from langchain_core.messages import SystemMessage

from onboarding.knowledge.informal_network.extraction import KnowledgeTriple, extract_triples

TEXTO = "Para Excel avanzado, preguntale a Diego. Es un genio."


def _triple(evidence: str) -> dict:
    return {
        "subject": "Diego",
        "relation": "knows_about",
        "object": "Excel avanzado",
        "evidence": evidence,
    }


def test_relacion_con_evidencia_textual_se_devuelve(structured_llm) -> None:
    modelo = structured_llm({"triples": [_triple("Para Excel avanzado, preguntale a Diego.")]})

    triples = extract_triples(TEXTO, modelo)

    assert triples == [
        KnowledgeTriple(
            subject="Diego",
            relation="knows_about",
            object="Excel avanzado",
            evidence="Para Excel avanzado, preguntale a Diego.",
        )
    ]


def test_relacion_con_evidencia_inventada_se_descarta(structured_llm) -> None:
    modelo = structured_llm({"triples": [_triple("Diego sabe mucho de Excel.")]})

    assert extract_triples(TEXTO, modelo) == []


def test_salida_vacia_del_modelo_devuelve_lista_vacia(structured_llm) -> None:
    assert extract_triples(TEXTO, structured_llm(None)) == []
    assert extract_triples(TEXTO, structured_llm({"triples": []})) == []


def test_el_prompt_lleva_organigrama_y_procedimientos(structured_llm) -> None:
    modelo = structured_llm(None)

    extract_triples(TEXTO, modelo)

    system = modelo.seen[0]
    assert isinstance(system, SystemMessage)
    assert "<organigrama>" in system.content
    assert "<procedimientos>" in system.content
    assert '<documento nombre="compras.md">' in system.content
    assert '<documento nombre="README.md">' not in system.content
    assert '<documento nombre="organigrama.md">' not in system.content


def test_sin_modelo_usa_el_del_proyecto(monkeypatch: pytest.MonkeyPatch, structured_llm) -> None:
    modelo = structured_llm({"triples": [_triple("Para Excel avanzado, preguntale a Diego.")]})
    monkeypatch.setattr(
        "onboarding.knowledge.informal_network.extraction.get_chat_model", lambda: modelo
    )

    assert len(extract_triples(TEXTO)) == 1
