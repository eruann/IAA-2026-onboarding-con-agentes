# producto
# Este archivo es parte del producto: el asistente de onboarding que se
# entrega y se evalúa.

"""El agente que responde las preguntas del ingresante. Titular: rol RAG y evaluación."""

from pathlib import Path

from langchain_core.language_models import BaseChatModel

from onboarding.agents.common import Node, NodeSpec, ask_model
from onboarding.agents.state import OnboardingState
from onboarding.knowledge import read_documents

PROMPT = Path(__file__).with_name("prompt.md")

# Transitorio: los documentos van enteros en el prompt, como en el primer chat del
# proyecto (PR #15). Se reemplaza por knowledge.retrieve (TODO de abajo).
CONTEXT_DOCUMENTS = ("organigrama.md", "tesoreria.md")


# recorrido: nodo-respuesta
def make_answer_question(model: BaseChatModel) -> Node:
    def answer_question(state: OnboardingState) -> dict:
        # TODO(rag): 1) knowledge.retrieve en vez de CONTEXT_DOCUMENTS
        # 2) responder citando documento y sección 3) si no hay soporte, no
        # inventar: derivar con knowledge.who_knows_about ("preguntale a X").
        context = f"<documentos>\n{read_documents(CONTEXT_DOCUMENTS)}\n</documentos>"
        return {
            "output": ask_model(model, PROMPT, state, context),
            "citations": [],
            "referred_to": None,
        }

    return answer_question


NODE = NodeSpec(
    "answer_question", "Responder pregunta", "RAG y evaluación", make_answer_question, PROMPT
)
