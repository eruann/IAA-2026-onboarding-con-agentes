"""El grafo se prueba con un modelo fake: sin red y determinístico.

Lo que se testea acá es el cableado (que cada intención llegue a su nodo), no la
calidad de la respuesta del modelo. Eso se mide en eval/.
"""

import typing
from pathlib import Path

import pytest
from langchain_core.language_models import FakeListChatModel

from onboarding.agents import build_graph
from onboarding.agents import graph as graph_module
from onboarding.agents.graph import NODES
from onboarding.agents.state import Intent


# recorrido: tests-grafo
def test_grafo_responde_pregunta_con_modelo_fake(fake_llm: FakeListChatModel) -> None:
    graph = build_graph(fake_llm)

    result = graph.invoke({"intent": "answer_question", "input": "¿cómo pido una compra?"})

    assert result["output"] == "respuesta de prueba"


def test_grafo_sin_intent_va_a_responder_pregunta(fake_llm: FakeListChatModel) -> None:
    graph = build_graph(fake_llm)

    result = graph.invoke({"input": "hola"})

    assert result["output"] == "respuesta de prueba"


# extract_knowledge no va acá: necesita un modelo con salida estructurada, que el
# fake no tiene. Lo prueba su propio test (agents/extract_knowledge/node_test.py).
@pytest.mark.parametrize("intent", ["generate_quest", "answer_question", "validate_evidence"])
def test_cada_intencion_llega_a_su_nodo(intent: str, fake_llm) -> None:
    graph = build_graph(fake_llm)

    result = graph.invoke({"intent": intent, "input": "texto"})

    assert result["output"]


def test_cada_agente_esta_una_vez_y_coincide_con_intent() -> None:
    names = [node.name for node in NODES]

    assert sorted(names) == sorted(typing.get_args(Intent))
    assert len(names) == len(set(names))


def test_cada_agente_tiene_su_carpeta_con_la_misma_forma() -> None:
    folder = Path(graph_module.__file__).parent
    for node in NODES:
        files = {path.name for path in (folder / node.name).iterdir()}
        assert {"__init__.py", "node.py", "node_test.py"} <= files, node.name
        # El prompt va al lado del código
        assert node.prompt == folder / node.name / "prompt.md"
        assert node.prompt.exists()
