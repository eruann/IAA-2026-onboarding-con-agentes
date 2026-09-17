"""El grafo se prueba con un modelo fake: sin red y determinístico.

Lo que se testea acá es el cableado (que cada intención llegue a su nodo), no la
calidad de la respuesta del modelo. Eso se mide en eval/.
"""

import pytest
from langchain_core.language_models import FakeListChatModel

from onboarding.agents import build_graph
from onboarding.agents.prompts import load_prompt


def test_grafo_responde_pregunta_con_modelo_fake(fake_llm: FakeListChatModel) -> None:
    graph = build_graph(fake_llm)

    result = graph.invoke({"intent": "answer_question", "input": "¿cómo pido una compra?"})

    assert result["output"] == "respuesta de prueba"


def test_grafo_sin_intent_va_a_responder_pregunta(fake_llm: FakeListChatModel) -> None:
    graph = build_graph(fake_llm)

    result = graph.invoke({"input": "hola"})

    assert result["output"] == "respuesta de prueba"


@pytest.mark.parametrize(
    "intent",
    ["generate_quest", "answer_question", "validate_evidence", "extract_knowledge"],
)
def test_cada_intencion_tiene_su_nodo_y_su_prompt(intent: str, fake_llm) -> None:
    graph = build_graph(fake_llm)

    result = graph.invoke({"intent": intent, "input": "texto"})

    assert result["output"]
    assert load_prompt(intent)
