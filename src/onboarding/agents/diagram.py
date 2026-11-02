"""Dibujo del grafo en Mermaid, con estilo "a mano" (como Excalidraw).

Sale del grafo compilado de verdad (`build_graph().get_graph()`), no de un dibujo
hecho aparte: si alguien suma un agente, aparece solo. Los nombres y colores
salen del registro. `visited` resalta el recorrido de un mensaje.
"""

from collections.abc import Sequence

from langchain_core.language_models import FakeListChatModel
from langgraph.graph import END, START

from onboarding.agents.graph import build_graph
from onboarding.agents.registry import BY_KEY

# Un color por rol, el mismo en todas las pantallas
ROLE_COLORS = {
    "Tech Lead": ("#f1f5f9", "#334155"),
    "RAG y evaluación": ("#dbeafe", "#1d4ed8"),
    "Grafo cultural y datos": ("#dcfce7", "#15803d"),
    "Experiencia": ("#fce7f3", "#be185d"),
    "Agentes y orquestación": ("#fef3c7", "#b45309"),
}
VISITED_COLOR = "#e11d48"

HEADER = """---
config:
  look: handDrawn
  theme: base
  themeVariables:
    fontFamily: "Kalam, 'Comic Sans MS', cursive"
    fontSize: 18px
    lineColor: "#334155"
---
flowchart LR"""


def _class_name(role: str) -> str:
    return "role" + "".join(word[:3].capitalize() for word in role.split())


def _node(key: str) -> str:
    if key == START:
        return f"  {key}((Inicio))"
    if key == END:
        return f"  {key}((Fin))"
    spec = BY_KEY[key]
    label = f'"{spec.title}<br/><small>{spec.role}</small>"'
    shape = {"router": "{{%s}}", "agent": "(%s)", "final": "[[%s]]"}[spec.kind]
    return f"  {key}{shape % label}"


# recorrido: dibujo-grafo
def graph_mermaid(visited: Sequence[str] = ()) -> str:
    """Mermaid del grafo. `visited`: nodos por los que pasó el último mensaje, en orden."""
    # El modelo no se usa para dibujar: el fake evita pedir una API key.
    graph = build_graph(FakeListChatModel(responses=[""])).get_graph()
    lines = [HEADER]
    lines += [_node(key) for key in graph.nodes]

    path = [START, *visited, END] if visited else []
    walked = set(zip(path, path[1:], strict=False))
    highlighted = []
    for index, edge in enumerate(graph.edges):
        arrow = "-.->" if edge.conditional else "-->"
        lines.append(f"  {edge.source} {arrow} {edge.target}")
        if (edge.source, edge.target) in walked:
            highlighted.append(index)

    for role, (fill, stroke) in ROLE_COLORS.items():
        lines.append(f"  classDef {_class_name(role)} fill:{fill},stroke:{stroke},color:#111827")
    for key in graph.nodes:
        if key in BY_KEY:
            lines.append(f"  class {key} {_class_name(BY_KEY[key].role)}")

    if visited:
        lines.append(f"  classDef visited stroke:{VISITED_COLOR},stroke-width:4px")
        lines.append(f"  class {','.join(visited)} visited")
    for index in highlighted:
        lines.append(f"  linkStyle {index} stroke:{VISITED_COLOR},stroke-width:3px")
    return "\n".join(lines)
