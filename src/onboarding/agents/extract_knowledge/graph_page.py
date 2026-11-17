# andamiaje
# Este archivo es andamiaje: una ayuda para que el equipo de estudiantes
# construya, pruebe o entienda el producto (talleres, diagramas, guías).
# No es parte del producto.

"""Ver el grafo: una página interactiva con el grafo real (data/informal_network.json),
que el taller de Grafo muestra embebida.

`graph_data` arma los nodos y las aristas ya listos para dibujar (nombres, colores y
estilo de línea según el estado); `graph_page.js` los dibuja con Cytoscape: se
arrastran los nodos, se hace zoom y al pasar el mouse se ve la frase. Solo lee el
grafo: no lo cambia.

La página pide el mismo acceso que los talleres. Se registra al importar este módulo
(lo importa `checks.py`, que es lo que importa el taller).
"""

import json
from pathlib import Path

from nicegui import ui

from onboarding.config import get_settings
from onboarding.knowledge import load_graph, person_profile
from onboarding.ui.access import has_test_access
from onboarding.ui.layout import load_session, setup_page

# Dónde se ve, dentro de la app (la interfaz cuelga de /ui)
GRAPH_PAGE = "/ui/talleres/grafo"

NODE_COLORS = {
    "person": "#3b82f6",
    "topic": "#10b981",
    "process": "#8b5cf6",
    "area": "#f59e0b",
    "conflict": "#ef4444",
}
NODE_TYPES = {
    "person": "persona",
    "topic": "tema",
    "process": "proceso",
    "area": "organización",
    "conflict": "conflicto",
}
RELATIONS = {
    "knows_about": "sabe de",
    "introduced": "presentó a",
    "belongs_to": "pertenece a",
    "owns_process": "es responsable de",
    "works_with": "trabaja con",
    "may_be_same": "¿misma persona?",
    "contradicts": "contradice",
}
CRITICALITIES = {"high": "alta", "medium": "media", "low": "baja"}
STATUSES = {0: "pendiente", 1: "confirmada", 2: "rechazada"}
CONFIRMED, REJECTED = 1, 2
# Lo deducido (la herramienta de algo que alguien hizo), para distinguirlo de lo dicho
INFERRED_COLOR = "#a855f7"

SCRIPT = (Path(__file__).with_name("graph_page.js")).read_text(encoding="utf-8")
CYTOSCAPE = "https://cdnjs.cloudflare.com/ajax/libs/cytoscape/3.28.1/cytoscape.min.js"


def graph_data(include_rejected: bool = False) -> dict:
    """Los nodos y las aristas del grafo real, listos para dibujar. Las rechazadas,
    solo si se piden; los nodos que quedan sin ninguna arista no se muestran."""
    graph = load_graph()
    edges = [e for e in graph["edges"] if include_rejected or e["status"] != REJECTED]
    used = {e["source"] for e in edges} | {e["target"] for e in edges}
    nodes = []
    for n in graph["nodes"]:
        if n["id"] not in used:
            continue
        organization = n.get("attributes", {}).get("organization", "")
        if n["type"] == "person" and not organization:
            # La de su nodo o, si es de la empresa, la del organigrama
            organization = person_profile(n["id"], n["id"]).organization
        nodes.append(
            {
                "id": n["id"],
                "name": n.get("name", n["id"]),
                "type": NODE_TYPES.get(n["type"], n["type"]),
                "color": NODE_COLORS.get(n["type"], "#64748b"),
                "organization": organization,
            }
        )
    return {"nodes": nodes, "edges": [_edge(e) for e in edges]}


def _edge(e: dict) -> dict:
    relation = RELATIONS.get(e["relation"], e["relation"])
    if e["status"] == REJECTED:
        color, line = "#9ca3af", "dotted"
    else:
        color = {"may_be_same": "#f97316", "contradicts": "#ef4444"}.get(e["relation"], "#64748b")
        if e.get("inferred"):
            color = INFERRED_COLOR
        line = "solid" if e["status"] == CONFIRMED else "dashed"
    return {
        "id": f"e{e['id']}",
        "source": e["source"],
        "target": e["target"],
        "label": f"#{e['id']} {relation}{' (deducida)' if e.get('inferred') else ''}",
        "status": STATUSES.get(e["status"], str(e["status"])),
        "criticality": CRITICALITIES.get(e.get("criticality") or "", ""),
        "evidence": e.get("evidence", ""),
        "note": e.get("review_note", ""),
        "color": color,
        "line": line,
    }


def _legend() -> str:
    colors = " · ".join(
        f'<span style="color:{NODE_COLORS[kind]}">●</span> {label}'
        for kind, label in NODE_TYPES.items()
    )
    return (
        f"{colors}<br>Línea llena: confirmada · rayada: pendiente · naranja: ¿misma "
        f'persona? · <span style="color:{INFERRED_COLOR}">violeta</span>: deducida · '
        "gris punteada: rechazada. Arrastrá los nodos, hacé zoom con la "
        "rueda y pasá el mouse por una flecha o un nodo para ver el detalle."
    )


@ui.page(GRAPH_PAGE.removeprefix("/ui"), response_timeout=20)
async def graph_page() -> None:
    dark = setup_page()
    ui.add_head_html(f'<script src="{CYTOSCAPE}"></script>')
    ui.add_head_html(f"<script>{SCRIPT}</script>")
    prefs = await load_session(dark)
    if not has_test_access(get_settings(), prefs):
        ui.label("Sin acceso: entrá a los talleres desde la entrada.")
        return

    def draw() -> None:
        data = json.dumps(graph_data(rejected.value), ensure_ascii=False)
        ui.run_javascript(f"drawInformalGraph({data})")

    with ui.row().classes("w-full items-center gap-4"):
        rejected = ui.switch("Mostrar las rechazadas", on_change=draw)
        ui.button("Recargar", icon="refresh", color=None, on_click=draw).props("outline").classes(
            "boton-borde"
        )
    ui.html(_legend()).classes("texto-suave text-sm")
    ui.element("div").props("id=grafo-detalle").classes("text-sm").style("min-height: 2.5em")
    ui.element("div").props("id=grafo-informal").classes("w-full").style(
        "height: 75vh; border: 1px solid rgba(49, 51, 63, 0.2); border-radius: 0.5rem"
    )
    draw()
