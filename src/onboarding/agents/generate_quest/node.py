"""Diseñador de misiones. Titular: rol Agentes y orquestación.

Crea misiones nuevas a partir de la documentación de un puesto. Propone: las
misiones del juego las siguen definiendo Experiencia y PM en data/quests.yaml.
"""

from langchain_core.language_models import BaseChatModel

from onboarding.agents.base import Node, ask
from onboarding.agents.state import OnboardingState


# recorrido: nodo-disenador
def make_node(model: BaseChatModel) -> Node:
    def generate_quest(state: OnboardingState) -> dict:
        # TODO(agentes): recuperar la documentación del puesto con
        # knowledge.retrieve y consultar knowledge.who_knows_about para saber a
        # quién involucrar. Devolver las misiones con el formato de data/quests.yaml.
        return {"output": ask(model, "generate_quest", state)}

    return generate_quest
