"""Grafo de LangGraph: coordinador → un agente → red informal.

Se arma solo desde el registro (`agents/registry.py`): un agente nuevo aparece en
el grafo sin tocar este archivo.

    START → coordinator → answer_question | quests | generate_quest → extract_knowledge → END
"""

from langchain_core.language_models import BaseChatModel
from langgraph.graph import END, START, StateGraph

from onboarding.agents.registry import BY_KEY, CHAT_AGENTS, FINAL, ROUTER
from onboarding.agents.state import OnboardingState
from onboarding.llm import get_chat_model


def _route(state: OnboardingState) -> str:
    agent = state["agent"]
    if agent not in BY_KEY or BY_KEY[agent].kind != "agent":
        valid = ", ".join(spec.key for spec in CHAT_AGENTS)
        raise ValueError(f"No existe el agente {agent!r}. Los que hay: {valid}")
    return agent


# recorrido: armado-grafo
def build_graph(model: BaseChatModel | None = None):
    """Compila el grafo. Los tests pasan un modelo fake; producción usa el default."""
    model = model or get_chat_model()

    builder = StateGraph(OnboardingState)
    for spec in (ROUTER, *CHAT_AGENTS, FINAL):
        builder.add_node(spec.key, spec.make_node(model))

    builder.add_edge(START, ROUTER.key)
    builder.add_conditional_edges(ROUTER.key, _route, {spec.key: spec.key for spec in CHAT_AGENTS})
    for spec in CHAT_AGENTS:
        builder.add_edge(spec.key, FINAL.key)
    builder.add_edge(FINAL.key, END)

    return builder.compile()
