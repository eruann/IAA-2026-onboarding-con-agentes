"""Grafo de LangGraph: misión → responder → validar evidencia → extraer conocimiento.

Por ahora el router manda cada intención a su nodo. Cuando los nodos se
implementen de verdad, acá se agregan los ciclos (por ejemplo: responder →
extraer conocimiento de la propia conversación).
"""

from langchain_core.language_models import BaseChatModel
from langgraph.graph import END, START, StateGraph

from onboarding.agents.nodes import (
    make_answer_question,
    make_extract_knowledge,
    make_generate_quest,
    make_validate_evidence,
)
from onboarding.agents.state import OnboardingState
from onboarding.llm import get_chat_model


def _route(state: OnboardingState) -> str:
    return state.get("intent", "answer_question")


def build_graph(model: BaseChatModel | None = None):
    """Compila el grafo. Los tests pasan un modelo fake; producción usa el default."""
    model = model or get_chat_model()

    builder = StateGraph(OnboardingState)
    builder.add_node("generate_quest", make_generate_quest(model))
    builder.add_node("answer_question", make_answer_question(model))
    builder.add_node("validate_evidence", make_validate_evidence(model))
    builder.add_node("extract_knowledge", make_extract_knowledge(model))

    builder.add_conditional_edges(
        START,
        _route,
        {
            "generate_quest": "generate_quest",
            "answer_question": "answer_question",
            "validate_evidence": "validate_evidence",
            "extract_knowledge": "extract_knowledge",
        },
    )
    for node in ("generate_quest", "answer_question", "validate_evidence", "extract_knowledge"):
        builder.add_edge(node, END)

    return builder.compile()
