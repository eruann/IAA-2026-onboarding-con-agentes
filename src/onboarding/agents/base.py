"""Lo que comparten todos los nodos.

Un nodo es una función que recibe el estado y devuelve **solo las claves que
cambia**. Se arma con `make_node(model)`: el modelo llega por parámetro, nunca se
crea adentro (así los tests pasan uno fake).
"""

from collections.abc import Callable

from langchain_core.language_models import BaseChatModel
from langchain_core.messages import BaseMessage, HumanMessage, SystemMessage

from onboarding.agents.prompts import load_prompt
from onboarding.agents.state import OnboardingState

Node = Callable[[OnboardingState], dict]


def ask(model: BaseChatModel, prompt_name: str, state: OnboardingState) -> str:
    """Le pasa al modelo el prompt del agente, la conversación previa y el texto del turno."""
    messages: list[BaseMessage] = [SystemMessage(load_prompt(prompt_name))]
    messages += state.get("messages", [])
    messages.append(HumanMessage(state.get("input", "")))
    return str(model.invoke(messages).content)
