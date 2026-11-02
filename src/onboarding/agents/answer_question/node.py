"""Agente de conocimiento. Titular: rol RAG y evaluación.

Responde las dudas del ingresante con lo que sabe la organización, por la única
puerta de la knowledge layer (`onboarding.knowledge`): primero lo escrito y, si
no alcanza, lo no escrito.
"""

from langchain_core.language_models import BaseChatModel

from onboarding.agents.base import Node, ask
from onboarding.agents.state import OnboardingState


# recorrido: nodo-respuesta
def make_node(model: BaseChatModel) -> Node:
    def answer_question(state: OnboardingState) -> dict:
        # TODO(rag): 1) knowledge.retrieve  2) responder citando documento y
        # sección  3) verificar la cita con knowledge.quote_is_supported
        # 4) si no hay soporte, no inventar: derivar con knowledge.who_knows_about
        # ("no tengo esta información, preguntale a X").
        return {
            "output": ask(model, "answer_question", state),
            "citations": [],
            "referred_to": None,
        }

    return answer_question
