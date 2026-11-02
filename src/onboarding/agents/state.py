"""Estado que viaja por el grafo."""

from typing import Annotated, Literal, TypedDict

from langchain_core.messages import AnyMessage
from langgraph.graph.message import add_messages

# Desde dónde habla la persona. Cambia qué puede pedir, no cómo se rutea.
Mode = Literal["employee", "manager", "test", "admin"]


# recorrido: estado-grafo
class OnboardingState(TypedDict, total=False):
    # A qué agente va el mensaje. Si viene vacío lo decide el coordinador; en el
    # modo Test lo elige quien prueba (ver agents/registry.py).
    agent: str
    mode: Mode
    # Quién habla: la key de data/people.yaml (people.key en la base)
    person_key: str | None
    # Conversación previa. add_messages las acumula en vez de pisarlas.
    messages: Annotated[list[AnyMessage], add_messages]
    # Texto de este turno (pregunta, evidencia, pedido del jefe)
    input: str
    # Salida para el usuario y de dónde salió
    output: str
    citations: list[str]
    # Cuando no hay soporte documental: a quién preguntarle
    referred_to: str | None
