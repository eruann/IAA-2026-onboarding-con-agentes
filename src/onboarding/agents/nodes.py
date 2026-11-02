# producto
# Este archivo es parte del producto: el asistente de onboarding que se
# entrega y se evalúa.

"""Nodos del grafo que todavía no tienen carpeta propia.

Cuando un rol empieza a trabajar su agente, lo pasa a `agents/<nodo>/` (como
`agents/extract_knowledge/`).

Todos tienen la misma forma: reciben el modelo por parámetro (nunca lo crean) y
devuelven las claves del estado que modifican.
"""

from collections.abc import Callable

from langchain_core.language_models import BaseChatModel
from langchain_core.messages import BaseMessage, HumanMessage, SystemMessage

from onboarding.agents.prompts import load_prompt
from onboarding.agents.state import OnboardingState
from onboarding.knowledge import read_documents

Node = Callable[[OnboardingState], dict]


def _ask(model: BaseChatModel, prompt_name: str, state: OnboardingState, context: str = "") -> str:
    """Prompt del agente (+ contexto opcional), conversación previa y texto del turno."""
    system = load_prompt(prompt_name)
    if context:
        system += f"\n\n{context}"
    if state.get("actor_name"):
        system += f"\n\nLa persona se llama {state['actor_name']}. Llamala por su nombre."
    messages: list[BaseMessage] = [SystemMessage(system), *state.get("messages", [])]
    messages.append(HumanMessage(state.get("input", "")))
    return str(model.invoke(messages).content)


def make_generate_quest(model: BaseChatModel) -> Node:
    def generate_quest(state: OnboardingState) -> dict:
        # TODO(agentes): recuperar documentación del rol con knowledge.retrieve y
        # consultar knowledge.who_knows_about para saber a quién involucrar.
        return {"output": _ask(model, "generate_quest", state)}

    return generate_quest


# Transitorio: los documentos van enteros en el prompt, como en el primer chat del
# proyecto (PR #15). Se reemplaza por knowledge.retrieve (TODO de abajo).
CONTEXT_DOCUMENTS = ("organigrama.md", "tesoreria.md")


# recorrido: nodo-respuesta
def make_answer_question(model: BaseChatModel) -> Node:
    def answer_question(state: OnboardingState) -> dict:
        # TODO(agentes): 1) knowledge.retrieve en vez de CONTEXT_DOCUMENTS
        # 2) responder citando documento y sección 3) si no hay soporte, no
        # inventar: derivar con knowledge.who_knows_about ("preguntale a X").
        context = f"<documentos>\n{read_documents(CONTEXT_DOCUMENTS)}\n</documentos>"
        return {
            "output": _ask(model, "answer_question", state, context),
            "citations": [],
            "referred_to": None,
        }

    return answer_question


def make_validate_evidence(model: BaseChatModel) -> Node:
    def validate_evidence(state: OnboardingState) -> dict:
        # TODO(agentes): decidir aprobada / rechazada / requiere revisión humana.
        # La aprobación final del jefe siempre gana sobre el agente.
        return {"output": _ask(model, "validate_evidence", state)}

    return validate_evidence
