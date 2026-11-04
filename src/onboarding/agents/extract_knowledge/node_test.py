"""El nodo y la extracción se prueban con un modelo de salida fija: sin red y
determinístico.

Lo que se testea acá es lo que hace el código alrededor del modelo (el filtro de
evidencia, el contexto que recibe y cómo arma la respuesta), no la calidad de la
extracción. Eso se mide en eval/.
"""

import pytest
from langchain_core.messages import SystemMessage

from onboarding.agents.common import Models
from onboarding.agents.extract_knowledge import extract_triples, make_extract_knowledge
from onboarding.agents.extract_knowledge.node import EXTRACTION_PROMPT, PROMPT
from onboarding.knowledge import KnowledgeTriple
from onboarding.llm import load_prompt

TEXTO = "Para Excel avanzado, preguntale a Diego. Es un genio."
RESPALDO = "Para Excel avanzado, preguntale a Diego."


def _triple(evidence: str) -> dict:
    return {
        "subject": "Diego",
        "relation": "knows_about",
        "object": "Excel avanzado",
        "evidence": evidence,
    }


def test_relacion_con_evidencia_textual_se_devuelve(structured_llm) -> None:
    modelo = structured_llm({"triples": [_triple(RESPALDO)]})

    triples = extract_triples(TEXTO, modelo)

    assert triples == [
        KnowledgeTriple(
            subject="Diego", relation="knows_about", object="Excel avanzado", evidence=RESPALDO
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
    modelo = structured_llm({"triples": [_triple(RESPALDO)]})
    node_module = "onboarding.agents.extract_knowledge.node"
    monkeypatch.setattr(f"{node_module}.get_structured_model", lambda: modelo)

    assert len(extract_triples(TEXTO)) == 1


def test_el_nodo_le_pasa_las_relaciones_a_su_prompt_y_cita_el_respaldo(structured_llm) -> None:
    modelo = structured_llm(
        {"triples": [_triple(RESPALDO)]}, reply="Registré que Diego sabe de Excel."
    )
    node = make_extract_knowledge(Models.same(modelo))

    result = node({"input": TEXTO, "actor_name": "Ana"})

    # La respuesta es la del agente, con su propio prompt (no el de la extracción)
    assert result == {"output": "Registré que Diego sabe de Excel.", "citations": [RESPALDO]}
    system = modelo.seen_reply[0].content
    assert system.startswith(load_prompt(PROMPT))
    assert f"- Diego sabe de Excel avanzado («{RESPALDO}»)" in system
    assert "La persona se llama Ana" in system
    # La extracción usó sus instrucciones, que no son las del agente
    assert modelo.seen[0].content.startswith(load_prompt(EXTRACTION_PROMPT))
    assert PROMPT != EXTRACTION_PROMPT


def test_sin_relaciones_el_agente_igual_responde(structured_llm) -> None:
    modelo = structured_llm({"triples": []}, reply="No encontré nada: ¿me das un ejemplo?")
    node = make_extract_knowledge(Models.same(modelo))

    result = node({"input": TEXTO})

    assert result == {"output": "No encontré nada: ¿me das un ejemplo?", "citations": []}
    assert "(ninguna con respaldo en el texto)" in modelo.seen_reply[0].content
