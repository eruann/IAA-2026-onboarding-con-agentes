# producto
# Este archivo es parte del producto: el asistente de onboarding que se
# entrega y se evalúa.

"""Un turno de conversación: la puerta de entrada al grafo para las interfaces.

La interfaz web lo usa hoy y Slack después. Quien llama no arma el estado: pasa
el texto, quién habla, la conversación previa y, si quiere, a qué nodo va.
"""

from collections.abc import Sequence
from dataclasses import dataclass, field
from typing import Literal

from langchain_core.language_models import BaseChatModel
from langchain_core.messages import AIMessage, BaseMessage, HumanMessage

from onboarding.agents.graph import build_graph
from onboarding.agents.state import Intent, OnboardingState

# Un mensaje previo de la conversación: quién lo dijo y qué dijo
Turn = tuple[Literal["user", "assistant"], str]


@dataclass(frozen=True)
class TurnResult:
    output: str
    # Los nodos por los que pasó el mensaje, en orden
    path: list[str] = field(default_factory=list)
    citations: list[str] = field(default_factory=list)


def _messages(history: Sequence[Turn]) -> list[BaseMessage]:
    return [HumanMessage(text) if who == "user" else AIMessage(text) for who, text in history]


# recorrido: run-turn
def run_turn(
    text: str,
    *,
    intent: Intent | None = None,
    actor_name: str | None = None,
    history: Sequence[Turn] = (),
    model: BaseChatModel | None = None,
) -> TurnResult:
    state: OnboardingState = {"input": text, "messages": _messages(history)}
    if intent:
        state["intent"] = intent
    if actor_name:
        state["actor_name"] = actor_name

    final: dict = {}
    path: list[str] = []
    # stream con "updates": un evento por nodo con lo que cambió. Así se sabe por
    # dónde pasó el mensaje, además de la respuesta.
    for event in build_graph(model).stream(state, stream_mode="updates"):
        for node, update in event.items():
            path.append(node)
            final.update(update or {})

    return TurnResult(
        output=final.get("output", ""), path=path, citations=final.get("citations", [])
    )
