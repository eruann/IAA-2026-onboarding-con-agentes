"""Nodos del grafo. Esqueleto: cada uno es un TODO del rol Agentes.

Todos tienen la misma forma: reciben el modelo por parámetro (nunca lo crean) y
devuelven las claves del estado que modifican.
"""

from collections.abc import Callable

from langchain_core.language_models import BaseChatModel
from langchain_core.messages import HumanMessage, SystemMessage

from onboarding.agents.prompts import load_prompt
from onboarding.agents.state import OnboardingState

Node = Callable[[OnboardingState], dict]


def _ask(model: BaseChatModel, prompt_name: str, user_text: str) -> str:
    messages = [SystemMessage(load_prompt(prompt_name)), HumanMessage(user_text)]
    return str(model.invoke(messages).content)


def make_generate_quest(model: BaseChatModel) -> Node:
    def generate_quest(state: OnboardingState) -> dict:
        # TODO(agentes): recuperar documentación del rol con knowledge.retrieve y
        # consultar knowledge.who_knows_about para saber a quién involucrar.
        return {"output": _ask(model, "generate_quest", state.get("input", ""))}

    return generate_quest


def make_answer_question(model: BaseChatModel) -> Node:
    def answer_question(state: OnboardingState) -> dict:
        # TODO(agentes): 1) knowledge.retrieve  2) responder citando fuente
        # 3) si no hay soporte, no inventar: derivar con knowledge.who_knows_about
        # ("no tengo esta información, preguntale a X").
        return {
            "output": _ask(model, "answer_question", state.get("input", "")),
            "citations": [],
            "referred_to": None,
        }

    return answer_question


def make_validate_evidence(model: BaseChatModel) -> Node:
    def validate_evidence(state: OnboardingState) -> dict:
        # TODO(agentes): decidir aprobada / rechazada / requiere revisión humana.
        # La aprobación final del jefe siempre gana sobre el agente.
        return {"output": _ask(model, "validate_evidence", state.get("input", ""))}

    return validate_evidence


def make_extract_knowledge(model: BaseChatModel) -> Node:
    def extract_knowledge(state: OnboardingState) -> dict:
        # TODO(agentes): salida estructurada y guardado en la red informal vía knowledge.
        return {"output": _ask(model, "extract_knowledge", state.get("input", ""))}

    return extract_knowledge
