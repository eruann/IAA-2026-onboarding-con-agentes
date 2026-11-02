"""Agente Mis misiones. Titular: rol Experiencia.

Trabaja con las misiones que ya existen: al ingresante le dice qué le falta,
recibe su evidencia y la valida; al jefe le cuenta cómo viene su equipo.
"""

from langchain_core.language_models import BaseChatModel

from onboarding.agents.base import Node, ask
from onboarding.agents.state import OnboardingState


# recorrido: nodo-misiones
def make_node(model: BaseChatModel) -> Node:
    def quests(state: OnboardingState) -> dict:
        # TODO(experiencia): con las funciones de game/ (misiones de la persona,
        # entregar evidencia, puntos) como tools. Validar la evidencia contra lo
        # que pide la misión: aprobada, revisión humana o incompleta. Si la
        # aprueba el jefe, el agente solo recomienda: decide la persona.
        return {"output": ask(model, "quests", state)}

    return quests
