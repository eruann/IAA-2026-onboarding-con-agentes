# producto
# Este archivo es parte del producto: el asistente de onboarding que se
# entrega y se evalúa.

"""Lo que comparten todos los agentes (nodos del grafo).

Cada agente vive en su carpeta `agents/<nodo>/`, siempre con la misma forma:
`node.py` (la función `make_<nodo>`), `node_test.py` y su `prompt.md`. Un nodo
recibe el modelo por parámetro (nunca lo crea) y devuelve solo las claves del
estado que modifica (`output`, `citations`, `referred_to`…).
"""

from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

from langchain_core.language_models import BaseChatModel
from langchain_core.messages import BaseMessage, HumanMessage, SystemMessage

from onboarding.agents.state import OnboardingState
from onboarding.llm import load_prompt

Node = Callable[[OnboardingState], dict]


@dataclass(frozen=True)
class NodeSpec:
    """Lo que hay que saber de un agente para armar el grafo y mostrarlo."""

    name: str  # el nodo en el grafo y el valor de `intent` que lo pide
    title: str  # cómo se llama en el dibujo del grafo
    role: str  # el rol dueño, como en docs/roles.md
    make: Callable[[BaseChatModel], Node]  # arma el nodo con el modelo
    prompt: Path  # su prompt.md, al lado de node.py


def ask_model(model: BaseChatModel, prompt: Path, state: OnboardingState, context: str = "") -> str:
    """Prompt del agente (+ contexto opcional), conversación previa y texto del turno."""
    system = load_prompt(prompt)
    if context:
        system += f"\n\n{context}"
    if state.get("actor_name"):
        system += f"\n\nLa persona se llama {state['actor_name']}. Llamala por su nombre."
    messages: list[BaseMessage] = [SystemMessage(system), *state.get("messages", [])]
    messages.append(HumanMessage(state.get("input", "")))
    return str(model.invoke(messages).content)
