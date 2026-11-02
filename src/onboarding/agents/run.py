"""Un turno de conversación: la única puerta de entrada al grafo.

La usan la interfaz web hoy y Slack después. Quien llama no arma el estado ni
conoce los nodos: pasa el texto, quién habla y, si quiere, a qué agente va.
"""

from collections.abc import Sequence
from dataclasses import dataclass, field
from typing import Literal

from langchain_core.language_models import BaseChatModel
from langchain_core.messages import AIMessage, BaseMessage, HumanMessage

from onboarding.agents.graph import build_graph
from onboarding.agents.state import Mode, OnboardingState

# Un mensaje previo de la conversación: quién lo dijo y qué dijo
Turn = tuple[Literal["user", "assistant"], str]


@dataclass(frozen=True)
class TurnResult:
    output: str
    agent: str  # el agente que atendió el turno
    citations: list[str] = field(default_factory=list)
    referred_to: str | None = None
    # Lo que devolvió cada nodo, en orden: el recorrido del mensaje por el grafo
    steps: list[tuple[str, dict]] = field(default_factory=list)

    @property
    def path(self) -> list[str]:
        return [node for node, _ in self.steps]


def _messages(history: Sequence[Turn]) -> list[BaseMessage]:
    return [HumanMessage(text) if who == "user" else AIMessage(text) for who, text in history]


# recorrido: run-turn
def run_turn(
    text: str,
    *,
    person_key: str | None = None,
    mode: Mode = "employee",
    agent: str | None = None,
    history: Sequence[Turn] = (),
    model: BaseChatModel | None = None,
) -> TurnResult:
    state: OnboardingState = {
        "input": text,
        "mode": mode,
        "person_key": person_key,
        "messages": _messages(history),
    }
    if agent:
        state["agent"] = agent

    final: dict = {}
    steps: list[tuple[str, dict]] = []
    # stream con "updates": un evento por nodo con lo que cambió. Con eso se
    # dibuja el recorrido y se ve qué devolvió cada agente.
    for event in build_graph(model).stream(state, stream_mode="updates"):
        for node, update in event.items():
            steps.append((node, update or {}))
            final.update(update or {})

    return TurnResult(
        output=final.get("output", ""),
        agent=final.get("agent", ""),
        citations=final.get("citations", []),
        referred_to=final.get("referred_to"),
        steps=steps,
    )
