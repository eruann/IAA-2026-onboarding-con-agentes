"""Orquestación de agentes con LangGraph. Titular: rol Agentes.

Interfaz pública del módulo: lo que otros módulos pueden importar.
"""

from onboarding.agents.graph import build_graph
from onboarding.agents.state import OnboardingState

# recorrido: agentes-interfaz
__all__ = ["OnboardingState", "build_graph"]
