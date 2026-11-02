# producto
# Este archivo es parte del producto: el asistente de onboarding que se
# entrega y se evalúa.

"""Estado que viaja por el grafo."""

from typing import Annotated, Literal, TypedDict

from langchain_core.messages import AnyMessage
from langgraph.graph.message import add_messages

Intent = Literal[
    "generate_quest",  # armar una misión para un rol
    "answer_question",  # responder una duda del ingresante con RAG
    "validate_evidence",  # revisar la evidencia de una misión completada
    "extract_knowledge",  # sacar "quién sabe qué" de una conversación
]


# recorrido: estado-grafo
class OnboardingState(TypedDict, total=False):
    intent: Intent
    # Quién habla (id de Slack), cómo se llama y en qué empresa/rol está
    actor_id: str
    actor_name: str
    role: str
    # Conversación previa. add_messages las acumula en vez de pisarlas.
    messages: Annotated[list[AnyMessage], add_messages]
    # Texto de entrada (pregunta, evidencia, mensaje del jefe)
    input: str
    # Salida para el usuario y de dónde salió
    output: str
    citations: list[str]
    # Cuando no hay soporte documental: a quién preguntarle
    referred_to: str | None
