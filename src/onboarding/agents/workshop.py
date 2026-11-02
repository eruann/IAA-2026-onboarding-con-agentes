# andamiaje
# Este archivo es andamiaje: una ayuda para que el equipo de estudiantes
# construya, pruebe o entienda el producto (talleres, diagramas, guías).
# No es parte del producto.

"""Taller del rol Agentes y orquestación.

El agente de este taller es el coordinador: el chat habla con él y él decide a qué
nodo va cada mensaje. Las pruebas revisan los agentes de los demás roles y cómo
encajan con el coordinador: que cada nodo cumpla lo que el coordinador espera, a
qué nodo iría un mensaje, una prueba A/B entre el coordinador y un nodo directo,
y una pregunta suelta a un nodo, con la opción de comparar dos modelos.
"""

import time
import typing
from pathlib import Path

from langchain_core.language_models import BaseChatModel, FakeListChatModel

from onboarding.agents.graph import build_graph, route
from onboarding.agents.run import TurnError, TurnResult, path_text, run_turn
from onboarding.agents.state import Intent, OnboardingState
from onboarding.llm import load_prompt
from onboarding.workshop import ChatHistory, Tool, Workshop, markdown_row

NODES: tuple[str, ...] = typing.get_args(Intent)
# De quién es cada nodo (docs/roles.md)
NODE_ROLES = {
    "answer_question": "RAG y evaluación",
    "generate_quest": "Diseñador de misiones",
    "validate_evidence": "Experiencia",
    "extract_knowledge": "Grafo cultural y datos",
}
# Lo que el coordinador espera que devuelva un nodo: claves del estado y su tipo
STATE_KEYS = set(OnboardingState.__annotations__)
SAMPLE_INPUT = "¿Quién es el jefe de Compras? Para Excel avanzado, preguntale a Diego."


def _fake_model() -> BaseChatModel:
    return FakeListChatModel(responses=["respuesta de prueba"])


def _contract_problems(update: object) -> list[str]:
    """Lo que no cumple lo que devolvió un nodo, según el estado del grafo."""
    if not isinstance(update, dict):
        return [f"devuelve {type(update).__name__}, no un dict"]
    problems = [f"{key} no es parte del estado" for key in update if key not in STATE_KEYS]
    output = update.get("output")
    if not isinstance(output, str) or not output.strip():
        problems.append("falta output (texto para la persona)")
    citations = update.get("citations", [])
    if not isinstance(citations, list) or not all(isinstance(c, str) for c in citations):
        problems.append("citations tiene que ser una lista de textos")
    referred = update.get("referred_to")
    if referred is not None and not isinstance(referred, str):
        problems.append("referred_to tiene que ser un nombre o None")
    return problems


def check_nodes(use_real_model: bool = False, model: BaseChatModel | None = None) -> str:
    """Corre cada nodo del grafo con un mensaje de ejemplo y revisa que devuelva lo
    que espera el coordinador. Salvo que se pida un modelo real, usa el fake: sin
    costo y sin red."""
    model = model if use_real_model and model else _fake_model()
    graph = build_graph(model).get_graph()
    state: OnboardingState = {"input": SAMPLE_INPUT, "messages": [], "actor_name": "Ana"}
    rows = []
    for node in NODES:
        start = time.perf_counter()
        try:
            update = graph.nodes[node].data.func(dict(state))
            problems = _contract_problems(update)
            result = "; ".join(problems) or "✅"
        except NotImplementedError as error:
            if "structured_output" in str(error):
                result = "ℹ️ el modelo fake no sabe salida estructurada: probalo con uno real"
            else:
                result = f"⏳ pendiente: {error}"
        except Exception as error:  # se muestra en la tabla, no corta la revisión
            result = f"❌ {type(error).__name__}: {str(error)[:160]}"
        seconds = time.perf_counter() - start
        rows.append(markdown_row((node, NODE_ROLES.get(node, "—"), result, f"{seconds:.1f} s")))
    which = "modelo fake" if isinstance(model, FakeListChatModel) else "modelo real"
    return "\n".join(
        [
            f"Mensaje de ejemplo: «{SAMPLE_INPUT}» · {which}",
            "",
            "| nodo | rol | revisión | tiempo |",
            "|---|---|---|---|",
            *rows,
        ]
    )


def route_message(message: str) -> str:
    """A qué nodo manda el coordinador un mensaje, sin correr el nodo."""
    node = route({"input": message, "messages": []})
    return f"El coordinador lo manda a **{node}** ({NODE_ROLES.get(node, '—')})."


def _run(question: str, history: tuple, intent: str | None, model) -> tuple[TurnResult, float]:
    start = time.perf_counter()
    try:
        result = run_turn(question, intent=intent, history=history, model=model)
    except TurnError as failure:
        # El error del modelo, no el del turno: así la interfaz lo explica
        raise failure.__cause__ from None
    return result, time.perf_counter() - start


def _side(title: str, result: TurnResult, seconds: float) -> str:
    return f"**{title}**\n\n{result.output}\n\n{path_text(result.path)} · **{seconds:.1f} s**"


def ab_test(
    node: Intent,
    question: str = "",
    history: ChatHistory = (),
    model: BaseChatModel | None = None,
) -> str:
    """Prueba A/B: la misma pregunta por el coordinador (A) y directo a un nodo (B).

    Sin pregunta, repite el último mensaje del chat del taller con la conversación
    que había antes.
    """
    if not question.strip():
        last = max((i for i, (who, _) in enumerate(history) if who == "user"), default=None)
        if last is None:
            raise ValueError("Escribí una pregunta o mandá un mensaje en el chat del taller.")
        question, history = history[last][1], history[:last]
    a, a_seconds = _run(question, history, None, model)
    b, b_seconds = _run(question, history, node, model)

    chosen = a.path[0] if a.path else "ninguno"
    same_node = (
        "✅ El coordinador eligió el mismo nodo."
        if chosen == node
        else f"⚠️ El coordinador eligió **{chosen}**; vos elegiste **{node}**."
    )
    same_answer = (
        "✅ Las respuestas son iguales."
        if a.output == b.output
        else "Las respuestas son distintas (con un modelo real puede pasar aunque vayan al "
        "mismo nodo)."
    )
    context = f"{len(history)} mensajes previos del chat" if history else "sin conversación previa"
    return "\n\n".join(
        [
            f"Pregunta: «{question}» · {context}",
            f"{same_node} {same_answer}",
            "---",
            _side("A · por el coordinador", a, a_seconds),
            "---",
            _side(f"B · directo a {node}", b, b_seconds),
        ]
    )


def show_prompt(node: Intent) -> str:
    """El prompt del nodo tal como lo recibe el modelo, antes del contexto y la
    conversación."""
    return f"`agents/prompts/{node}.md`\n\n```markdown\n{load_prompt(node)}\n```"


def ask_node(node: Intent, question: str, model: BaseChatModel | None = None) -> str:
    """Una pregunta suelta a un nodo: la respuesta, por dónde pasó y cuánto tardó."""
    result, seconds = _run(question, (), node, model)
    return f"{result.output}\n\n---\n\n{path_text(result.path)} · **{seconds:.1f} s**"


# recorrido: taller-agentes
WORKSHOP = Workshop(
    role="Agentes y orquestación",
    intent=None,  # el chat habla con el coordinador, que decide el nodo
    summary=(
        "El coordinador, que decide a qué agente va cada mensaje, y la revisión de los "
        "agentes de los demás roles: que encajen con el coordinador y respondan bien. "
        "Chateá con el coordinador y compará contra cada nodo."
    ),
    tools=(
        Tool(
            check_nodes,
            "Revisar los nodos",
            "Corre cada nodo y revisa que devuelva lo que espera el coordinador. Usa el "
            "modelo fake (sin costo) salvo que prendas use_real_model.",
        ),
        Tool(route_message, "¿A qué nodo iría?", "Escribí un mensaje: qué decide el coordinador."),
        Tool(
            ab_test,
            "Coordinador contra nodo directo (A/B)",
            "La misma pregunta por el coordinador y directo al nodo que elijas. Si dejás la "
            "pregunta vacía, repite tu último mensaje del chat con la conversación de antes.",
        ),
        Tool(
            ask_node,
            "Preguntarle a un nodo",
            "Una pregunta suelta a un nodo. Con «Comparar con otro modelo» ves dos "
            "respuestas lado a lado, con lo que tardó cada una.",
        ),
        Tool(show_prompt, "Ver el prompt de un nodo", "Elegí un nodo."),
    ),
    guide=Path(__file__).parent / "LEEME.md",
)
