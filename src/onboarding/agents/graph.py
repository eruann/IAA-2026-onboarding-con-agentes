# producto
# Este archivo es parte del producto: el asistente de onboarding que se
# entrega y se evalúa.

"""El grafo de LangGraph: el coordinador elige a qué agente va cada mensaje.

Hoy es un ruteo: el coordinador (`route`) manda cada mensaje a un nodo y ese nodo
termina el turno. Los agentes se declaran una sola vez, en `NODES`; de ahí salen
el grafo, el dibujo y la tabla del taller de Agentes.
"""

from langchain_core.language_models import BaseChatModel
from langgraph.graph import END, START, StateGraph

from onboarding.agents import answer_question, extract_knowledge, generate_quest, validate_evidence
from onboarding.agents.common import Models, NodeSpec
from onboarding.agents.state import OnboardingState
from onboarding.llm import get_chat_model, get_structured_model

# Los agentes del grafo, uno por rol (docs/roles.md). Sumar uno: su carpeta en
# agents/<nodo>/, su valor en `Intent` (state.py) y su NODE acá.
NODES: tuple[NodeSpec, ...] = (
    generate_quest.NODE,
    answer_question.NODE,
    validate_evidence.NODE,
    extract_knowledge.NODE,
)


def route(state: OnboardingState) -> str:
    """El coordinador: a qué nodo va el mensaje. Hoy, el que pide `intent`; sin
    `intent`, a responder preguntas."""
    return state.get("intent", "answer_question")


# recorrido: armado-grafo
def build_graph(model: BaseChatModel | None = None, structured: BaseChatModel | None = None):
    """Compila el grafo. Cada nodo recibe un modelo por perfil: `model` (el principal,
    el del .env si no viene) y `structured` (el de LLM_STRUCTURED_MODEL o, si no hay,
    el principal). Los tests pasan un modelo fake."""
    model = model or get_chat_model()
    models = Models(model, structured or get_structured_model(model))

    builder = StateGraph(OnboardingState)
    for node in NODES:
        builder.add_node(node.name, node.make(models))
        builder.add_edge(node.name, END)
    builder.add_conditional_edges(START, route, {node.name: node.name for node in NODES})
    return builder.compile()
