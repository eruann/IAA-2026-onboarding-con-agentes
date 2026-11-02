"""Coordinador. Titular: Tech Lead.

Hoy es tonto a propósito: si el mensaje trae `agent` (en el modo Test lo elige
quien prueba) lo respeta; si no, manda todo al agente de conocimiento.
"""

from langchain_core.language_models import BaseChatModel

from onboarding.agents.base import Node
from onboarding.agents.state import OnboardingState

DEFAULT_AGENT = "answer_question"


# recorrido: coordinador
def make_node(model: BaseChatModel) -> Node:
    def coordinator(state: OnboardingState) -> dict:
        # TODO(tech-lead): sin agente elegido, clasificar el mensaje con el modelo
        # usando la descripción de cada agente del registro (agents/registry.py).
        return {"agent": state.get("agent") or DEFAULT_AGENT}

    return coordinator
