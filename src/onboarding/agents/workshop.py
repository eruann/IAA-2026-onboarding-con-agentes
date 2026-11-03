# andamiaje
# Este archivo es andamiaje: una ayuda para que el equipo de estudiantes
# construya, pruebe o entienda el producto (talleres, diagramas, guías).
# No es parte del producto.

"""Taller del rol Agentes y orquestación.

El agente de este taller es el coordinador: el chat habla con él y él decide a qué
nodo va cada mensaje. Las pruebas (en `checks.py`) revisan los agentes de los
demás roles y cómo encajan con el coordinador.
"""

from pathlib import Path

# 1. Pruebas ad hoc (andamiaje): checks.py de este agente
from onboarding.agents.checks import ab_test, ask_node, check_nodes, route_message, show_prompt

# 2. Del agente (producto): node.py de este agente
# (ninguna: el coordinador es route, en graph.py, y se prueba con el chat)
# 3. Del código común (producto): knowledge layer, game y demás interfaces
from onboarding.workshop import Tool, Workshop

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
