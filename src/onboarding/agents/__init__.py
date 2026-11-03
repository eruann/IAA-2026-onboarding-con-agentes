# producto
# Este archivo es parte del producto: el asistente de onboarding que se
# entrega y se evalúa.

"""Orquestación de agentes con LangGraph. Titular: rol Agentes.

Interfaz pública del módulo: lo que otros módulos pueden importar.
"""

from onboarding.agents.diagram import knowledge_used_by, load_lineage
from onboarding.agents.graph import build_graph
from onboarding.agents.run import TurnError, TurnResult, path_text, run_turn
from onboarding.agents.state import OnboardingState

# recorrido: agentes-interfaz
__all__ = [
    "OnboardingState",
    "TurnError",
    "TurnResult",
    "build_graph",
    "knowledge_used_by",
    "load_lineage",
    "path_text",
    "run_turn",
]
