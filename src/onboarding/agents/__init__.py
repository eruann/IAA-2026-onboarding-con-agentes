"""Orquestación de agentes con LangGraph.

Interfaz pública del módulo: lo que otros módulos pueden importar. Cada agente
vive en su carpeta (`agents/<agente>/`) y se suma al grafo desde
`agents/registry.py`.
"""

from onboarding.agents.diagram import graph_mermaid
from onboarding.agents.graph import build_graph
from onboarding.agents.registry import AGENTS, BY_KEY, CHAT_AGENTS, AgentSpec
from onboarding.agents.run import TurnResult, run_turn
from onboarding.agents.state import Mode, OnboardingState
from onboarding.agents.status import is_pending
from onboarding.agents.workshop import WORKSHOPS

# recorrido: agentes-interfaz
__all__ = [
    "AGENTS",
    "BY_KEY",
    "CHAT_AGENTS",
    "WORKSHOPS",
    "AgentSpec",
    "Mode",
    "OnboardingState",
    "TurnResult",
    "build_graph",
    "graph_mermaid",
    "is_pending",
    "run_turn",
]
