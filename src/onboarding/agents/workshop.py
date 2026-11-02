# andamiaje
# Este archivo es andamiaje: una ayuda para que el equipo de estudiantes
# construya, pruebe o entienda el producto (talleres, diagramas, guías).
# No es parte del producto.

"""Taller del rol Agentes y orquestación.

Declara las pruebas: ver el prompt de cada nodo y preguntarle a un nodo midiendo
cuánto tarda, con la opción de comparar dos modelos lado a lado. El chat deja
elegir el nodo. Cómo se arma el grafo y cómo responde cada nodo está en
`graph.py`, `run.py`, `nodes.py` y las carpetas de cada nodo.
"""

import time
import typing
from pathlib import Path

from langchain_core.language_models import BaseChatModel

from onboarding.agents.run import TurnError, path_text, run_turn
from onboarding.agents.state import Intent
from onboarding.llm import load_prompt
from onboarding.workshop import Tool, Workshop

NODES: tuple[str, ...] = typing.get_args(Intent)


def show_prompt(node: Intent) -> str:
    """El prompt del nodo tal como lo recibe el modelo, antes del contexto y la
    conversación."""
    return f"`agents/prompts/{node}.md`\n\n```markdown\n{load_prompt(node)}\n```"


def ask_node(node: Intent, question: str, model: BaseChatModel | None = None) -> str:
    """Una pregunta suelta a un nodo: la respuesta, por dónde pasó y cuánto tardó."""
    start = time.perf_counter()
    try:
        result = run_turn(question, intent=node, model=model)
    except TurnError as failure:
        # El error del modelo, no el del turno: así la interfaz lo explica
        raise failure.__cause__ from None
    seconds = time.perf_counter() - start
    return f"{result.output}\n\n---\n\n{path_text(result.path)} · **{seconds:.1f} s**"


# recorrido: taller-agentes
WORKSHOP = Workshop(
    role="Agentes y orquestación",
    intent="answer_question",
    intents=tuple(node for node in NODES if node != "answer_question"),
    summary=(
        "El coordinador y el grafo que une a los agentes de todos los roles, las tools "
        "compartidas, los prompts y la comparación de modelos por costo y latencia. "
        "Chateá con cualquier nodo y compará modelos."
    ),
    tools=(
        Tool(show_prompt, "Ver el prompt de un nodo", "Elegí un nodo."),
        Tool(
            ask_node,
            "Preguntarle a un nodo",
            "Elegí un nodo y escribí una pregunta. Con «Comparar con otro modelo» ves "
            "dos respuestas lado a lado, con lo que tardó cada una.",
        ),
    ),
    guide=Path(__file__).parent / "LEEME.md",
)
