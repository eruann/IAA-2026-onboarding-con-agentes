"""Nodo de la red informal. Titular: rol Grafo cultural y datos.

Corre al final de **todos** los turnos, venga del agente que venga, y no le
contesta nada al usuario: lee la conversación y guarda quién sabe qué. Así toda
pregunta y toda aprobación alimentan la red informal.
"""

from langchain_core.language_models import BaseChatModel

from onboarding.agents.base import Node
from onboarding.agents.state import OnboardingState


# recorrido: nodo-red-informal
def make_node(model: BaseChatModel) -> Node:
    def extract_knowledge(state: OnboardingState) -> dict:
        # TODO(grafo): extract_triples sobre la pregunta y la respuesta del turno
        # y guardar las relaciones (con su frase de respaldo) en nodes/edges.
        # No devuelve `output`: la respuesta al usuario ya la dio otro agente.
        return {}

    return extract_knowledge
