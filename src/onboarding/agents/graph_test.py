"""El grafo se prueba con un modelo fake: sin red y determinístico.

Lo que se testea acá es el cableado (que cada mensaje llegue a su agente y que
la red informal corra siempre al final), no la calidad de la respuesta del
modelo. Eso se mide en eval/.
"""

import pytest
from langchain_core.language_models import FakeListChatModel

from onboarding.agents import CHAT_AGENTS, build_graph


# recorrido: tests-grafo
def test_sin_agente_elegido_va_a_conocimiento(fake_llm: FakeListChatModel) -> None:
    graph = build_graph(fake_llm)

    result = graph.invoke({"input": "¿cómo pido una compra?"})

    assert result["agent"] == "answer_question"
    assert result["output"] == "respuesta de prueba"


@pytest.mark.parametrize("agent", [spec.key for spec in CHAT_AGENTS])
def test_cada_agente_elegido_responde(agent: str, fake_llm: FakeListChatModel) -> None:
    graph = build_graph(fake_llm)

    result = graph.invoke({"agent": agent, "input": "texto"})

    assert result["agent"] == agent
    assert result["output"]


def test_la_red_informal_corre_al_final_de_cada_turno(fake_llm: FakeListChatModel) -> None:
    graph = build_graph(fake_llm)

    nodes = [
        node
        for event in graph.stream({"agent": "quests", "input": "hola"}, stream_mode="updates")
        for node in event
    ]

    assert nodes == ["coordinator", "quests", "extract_knowledge"]


def test_agente_inexistente_falla_con_mensaje_claro(fake_llm: FakeListChatModel) -> None:
    graph = build_graph(fake_llm)

    with pytest.raises(ValueError, match="No existe el agente 'cualquiera'"):
        graph.invoke({"agent": "cualquiera", "input": "hola"})
