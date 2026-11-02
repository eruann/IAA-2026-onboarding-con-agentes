# producto
# Este archivo es parte del producto: el asistente de onboarding que se
# entrega y se evalúa.

"""Nodo que propone misiones nuevas. Titular: rol Diseñador de misiones.

Propone borradores de misiones para un puesto a partir de su documentación. No
toca el juego: cuáles entran a `data/quests.yaml` lo deciden Experiencia y PM.
"""

from langchain_core.language_models import BaseChatModel

from onboarding.agents.nodes import Node, ask_model
from onboarding.agents.state import OnboardingState


# recorrido: nodo-misiones
def make_generate_quest(model: BaseChatModel) -> Node:
    def generate_quest(state: OnboardingState) -> dict:
        # TODO(misiones): recuperar documentación del rol con knowledge.retrieve y
        # consultar knowledge.who_knows_about para saber a quién involucrar.
        # Devolver las misiones con la forma de Quest (ver game/quests.py).
        return {"output": ask_model(model, "generate_quest", state)}

    return generate_quest
