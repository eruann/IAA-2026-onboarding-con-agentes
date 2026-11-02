"""Registro de agentes: la única lista de qué nodos hay y de quién es cada uno.

De acá salen el grafo (`graph.py`), el selector de agentes y las fichas de la
interfaz, el dibujo del grafo y, más adelante, lo que lee el coordinador para
elegir. Sumar un agente es sumar una entrada a `AGENTS`.
"""

import inspect
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

from langchain_core.language_models import BaseChatModel

from onboarding.agents import (
    answer_question,
    coordinator,
    extract_knowledge,
    generate_quest,
    quests,
)
from onboarding.agents.base import Node
from onboarding.knowledge import extract_triples, quote_is_supported, retrieve, who_knows_about

# router: decide a quién va el mensaje. agent: responde al usuario.
# final: corre después de cualquier agente, sin responder.
Kind = Literal["router", "agent", "final"]


@dataclass(frozen=True)
class AgentSpec:
    key: str  # nombre del nodo en el grafo y del prompt en agents/prompts/
    title: str  # cómo se ve en la interfaz
    role: str  # rol del equipo que lo construye
    kind: Kind
    description: str  # qué hace, en una línea
    receives: str
    returns: str
    make_node: Callable[[BaseChatModel], Node]
    # Funciones de otros módulos que el agente necesita: la interfaz muestra si
    # ya están implementadas o siguen en TODO.
    uses: tuple[Callable, ...] = ()

    @property
    def code_file(self) -> Path:
        return Path(inspect.getfile(self.make_node))


# recorrido: registro-agentes
AGENTS: tuple[AgentSpec, ...] = (
    AgentSpec(
        key="coordinator",
        title="Coordinador",
        role="Tech Lead",
        kind="router",
        description="Decide a qué agente va cada mensaje.",
        receives="el mensaje y, si se eligió, el agente",
        returns="el agente que atiende el turno",
        make_node=coordinator.make_node,
    ),
    AgentSpec(
        key="answer_question",
        title="Conocimiento",
        role="RAG y evaluación",
        kind="agent",
        description=(
            "Responde dudas sobre la empresa citando la documentación; si no hay "
            "respaldo, deriva a quien sabe del tema."
        ),
        receives="la pregunta y quién la hace",
        returns="respuesta, fuentes citadas y a quién derivó",
        make_node=answer_question.make_node,
        uses=(retrieve, quote_is_supported, who_knows_about),
    ),
    AgentSpec(
        key="quests",
        title="Mis misiones",
        role="Experiencia",
        kind="agent",
        description=(
            "Acompaña en las misiones existentes: qué falta, recibir y validar "
            "evidencia, puntos; al jefe, cómo viene su equipo."
        ),
        receives="el mensaje, quién habla y su modo (empleado o jefe)",
        returns="respuesta y, si hubo evidencia, si se aprueba o pasa a revisión",
        make_node=quests.make_node,
    ),
    AgentSpec(
        key="generate_quest",
        title="Diseñador de misiones",
        role="Agentes y orquestación",
        kind="agent",
        description="Propone misiones nuevas a partir de la documentación de un puesto.",
        receives="el puesto o el pedido del jefe",
        returns="misiones con título, pasos, evidencia y quién aprueba",
        make_node=generate_quest.make_node,
        uses=(retrieve, who_knows_about),
    ),
    AgentSpec(
        key="extract_knowledge",
        title="Red informal",
        role="Grafo cultural y datos",
        kind="final",
        description="Después de cada turno extrae quién sabe qué y lo guarda en la red informal.",
        receives="la pregunta y la respuesta del turno",
        returns="nada al usuario: guarda relaciones con su frase de respaldo",
        make_node=extract_knowledge.make_node,
        uses=(extract_triples,),
    ),
)

BY_KEY = {spec.key: spec for spec in AGENTS}
ROUTER = next(spec for spec in AGENTS if spec.kind == "router")
FINAL = next(spec for spec in AGENTS if spec.kind == "final")
CHAT_AGENTS = tuple(spec for spec in AGENTS if spec.kind == "agent")
