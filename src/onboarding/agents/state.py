"""Estado que viaja por el grafo."""

from typing import Literal, TypedDict

Intent = Literal[
    "generate_quest",  # armar una misión para un rol
    "answer_question",  # responder una duda del ingresante con RAG
    "validate_evidence",  # revisar la evidencia de una misión completada
    "extract_knowledge",  # sacar "quién sabe qué" de una conversación
]


class OnboardingState(TypedDict, total=False):
    intent: Intent
    # Quién habla (id de Slack) y en qué empresa/rol está
    actor_id: str
    role: str
    # Texto de entrada (pregunta, evidencia, mensaje del jefe)
    input: str
    # Salida para el usuario y de dónde salió
    output: str
    citations: list[str]
    # Cuando no hay soporte documental: a quién preguntarle
    referred_to: str | None
