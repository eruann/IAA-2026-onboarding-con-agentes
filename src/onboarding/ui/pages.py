# andamiaje
# Este archivo es andamiaje: una ayuda para que el equipo de estudiantes
# construya, pruebe o entienda el producto (talleres, diagramas, guías).
# No es parte del producto.

"""Los talleres (`/ui/talleres`): uno por rol, con el chat de su agente, sus
pruebas, el grafo y su guía. Se entra con el botón Test de la entrada (ver
access.py)."""

import json
from collections.abc import Callable, Sequence
from pathlib import Path

from nicegui import run, ui

from onboarding.agents import knowledge_used_by, load_lineage
from onboarding.config import get_settings
from onboarding.llm import model_catalog
from onboarding.ui.access import has_test_access
from onboarding.ui.chat import chat
from onboarding.ui.layout import load_session, page_frame, setup_page, sidebar
from onboarding.ui.tool_form import tool_card
from onboarding.workshop import UPCOMING, Embed, Workshop, all_workshops

GRAPH_STYLE = """<style>
  /* El grafo va sobre una "pizarra" blanca también en modo oscuro */
  .pizarra { background: #ffffff; border-radius: 0.75rem; padding: 0.5rem; }
  /* Recorrido del último mensaje: solo el borde de cada caja (el último trazo
     que dibuja rough.js; el primero es el relleno) y las líneas */
  .pizarra [data-id].resaltado:not(.flecha) > g > path:last-of-type,
  .pizarra .flecha.resaltado path { stroke: #e11d48; stroke-width: 3; transition: stroke 0.2s; }
  /* Donde falló el último mensaje, y lo que usó la última prueba del taller */
  .pizarra [data-id].fallido > g > path:last-of-type {
    stroke: #e11d48; stroke-width: 4; stroke-dasharray: 8 5;
  }
  .pizarra [data-id].en-uso > g > path:last-of-type { stroke: #7c3aed; stroke-width: 3; }
</style>"""


def _workshop_select(workshops: list[Workshop], current: int) -> None:
    options = {index: item.role for index, item in enumerate(workshops)}
    options |= {f"proximo-{role}": f"{role} · próximamente" for role in UPCOMING}

    def on_workshop_change(event) -> None:
        if isinstance(event.value, int):
            ui.navigate.to(f"?taller={event.value}")
        else:
            ui.notify("Ese taller todavía no existe: se suma en los próximos PRs.")
            event.sender.value = current

    ui.select(options, label="Taller", value=current, on_change=on_workshop_change).classes(
        "w-full"
    )


# Dibuja el grafo como diagrama de flujo con trazo a mano (ELK + rough.js, ver ui/grafo.js)
GRAPH_JS = (Path(__file__).parent / "grafo.js").read_text(encoding="utf-8")
GRAPH_NOTICE = (
    "ⓘ Generado automáticamente desde el código. Es una guía para orientarse: puede tener errores."
)
GRAPH_LEGEND = (
    "**Amarillo**: nodos del grafo · **Rombo**: elige el nodo según la tarea · "
    "**Línea celeste punteada**: qué usa cada nodo de la knowledge layer · "
    "**Azul**: función usada por el grafo · **Rojo**: todavía es un TODO · "
    "**Naranja**: nadie la usa · **Gris**: se usa fuera del grafo (ingesta, seed) · "
    "**⚙ modelo**: llama al modelo · **Borde rojo**: recorrido del último mensaje · "
    "**Borde rojo punteado**: donde falló · **Borde violeta**: lo que usó la última prueba. "
    "Rueda del mouse: zoom · arrastrar: mover · doble clic: ver todo."
)
CHECK_ICONS = {True: "✅", False: "❌", None: "ℹ️"}


def _checks(lineage: dict) -> None:
    """Los chequeos de reglas del lineage, para ver de un vistazo si algo se rompió."""
    for check in lineage["chequeos"]:
        detail = ", ".join(check["detalle"]) if check["detalle"] else "sin problemas"
        # Texto común y no Markdown: los nombres con "_" se verían en cursiva
        ui.label(f"{CHECK_ICONS[check['ok']]} {check['regla']}: {detail}").classes(
            "text-caption q-mb-sm"
        )


# recorrido: panel-grafo
def _graph_panel():
    """Panel a la derecha con el grafo completo (sale de agents/grafo.json), con
    botón para ampliarlo. Devuelve dos funciones: una marca el recorrido de un mensaje
    y la otra lo que usó una prueba."""
    lineage = load_lineage()
    # Lo último marcado, para repetirlo al ampliar
    last = {"path": [], "failed": None, "uses": []}

    def drawing_area(*classes: str):
        ui.label(GRAPH_NOTICE).classes("texto-suave text-caption")
        area = ui.element("div").classes("pizarra w-full " + " ".join(classes))
        ui.markdown(GRAPH_LEGEND).classes("texto-suave text-caption")
        return area

    with ui.dialog().props("maximized") as big, ui.card().classes("w-full h-full q-pa-md"):
        with ui.row().classes("w-full items-center"):
            ui.label("Grafo de agentes").classes("text-h6")
            ui.space()
            ui.button(icon="close", on_click=big.close).props("flat round")
        big_drawing = drawing_area().props('data-alto="75vh"')

    with ui.right_drawer(value=False).props("width=620").classes("sidebar q-pa-md") as panel:
        with ui.row().classes("w-full items-center"):
            ui.label("Grafo de agentes").classes("text-h6")
            ui.space()
            ui.button(
                "Ampliar", icon="open_in_full", color=None, on_click=lambda: open_big()
            ).props("outline").classes("boton-borde")
        ui.label(
            "El grafo completo y lo que usa cada nodo. Después de cada mensaje se "
            "marca por dónde pasó; después de cada prueba, qué usó."
        ).classes("texto-suave text-caption")
        drawing = drawing_area()
        with ui.expansion("Chequeos de reglas", icon="rule").classes("w-full seccion"):
            _checks(lineage)
    with ui.page_sticky(position="top-right", x_offset=16, y_offset=16):
        ui.button("Grafo", icon="account_tree", on_click=panel.toggle).props("outline")

    def draw(target) -> None:
        args = [lineage, last["path"], last["failed"], last["uses"]]
        ui.run_javascript(f"dibujarGrafo('c{target.id}', {', '.join(map(json.dumps, args))})")

    def open_big() -> None:
        big.open()
        draw(big_drawing)

    def mark(path: Sequence[str], failed: str | None = None) -> None:
        last.update(path=list(path), failed=failed)
        for target in (drawing, big_drawing):
            ui.run_javascript(
                f"marcarRecorrido('c{target.id}', {json.dumps(list(path))}, {json.dumps(failed)})"
            )

    def mark_uses(fn: Callable) -> None:
        last["uses"] = knowledge_used_by(fn)
        for target in (drawing, big_drawing):
            ui.run_javascript(f"marcarUso('c{target.id}', {json.dumps(last['uses'])})")

    draw(drawing)
    return mark, mark_uses


def _embed(embed: Embed) -> None:
    """Una página de la app dentro del taller (p. ej. el panel del jefe), con botón
    para recargarla después de cambiar su código."""
    with ui.expansion(embed.title, icon="web").classes("w-full seccion"):
        if embed.help:
            ui.label(embed.help).classes("texto-suave")
        frame = page_frame(embed.path)
        with ui.row().classes("items-center gap-4"):
            ui.button(
                "Recargar",
                icon="refresh",
                color=None,
                on_click=lambda: ui.run_javascript(
                    f"const f = document.getElementById('c{frame.id}'); f.src = f.src"
                ),
            ).props("outline").classes("boton-borde")
            ui.link("Abrir en otra pestaña", embed.path, new_tab=True)


# recorrido: pagina-talleres
@ui.page("/talleres", response_timeout=20)
async def talleres(taller: int = 0) -> None:
    dark = setup_page()
    ui.add_head_html(GRAPH_STYLE)
    ui.add_head_html(f'<script type="module">{GRAPH_JS}</script>')
    # Las preferencias viven en el navegador: hay que esperar a que se conecte
    prefs = await load_session(dark)
    if not has_test_access(get_settings(), prefs):
        ui.navigate.to("./")  # a la entrada, que pide la clave si hace falta
        return
    name = prefs.get("name") or "equipo"

    workshops = all_workshops()
    current = min(max(taller, 0), len(workshops) - 1)
    workshop = workshops[current]
    # La lista de modelos sale de OpenRouter y de Ollama: se pide fuera del hilo
    # principal para no trabar la página.
    catalog = await run.io_bound(model_catalog)
    models = catalog.options
    model_select = sidebar(
        prefs,
        catalog,
        dark,
        title=f"Talleres · {name}",
        extra=lambda: _workshop_select(workshops, current),
    )
    mark_path, mark_uses = _graph_panel()

    # Una sola pantalla: el chat abierto y el resto en secciones que se despliegan
    with ui.column().classes("w-full max-w-3xl mx-auto q-px-md q-py-xl gap-4"):
        ui.label(workshop.role).classes("titulo")
        ui.label(workshop.summary).classes("texto-suave")
        with ui.expansion("Chat", icon="chat", value=True).classes("w-full seccion"):
            history = chat(
                models,
                model_select,
                name,
                intent=workshop.intent,
                on_turn=mark_path,
                greeting=workshop.greeting,
            )
        with ui.expansion("Pruebas", icon="science").classes("w-full seccion"):
            for tool in workshop.tools:
                tool_card(
                    tool,
                    models,
                    model_select.value,
                    on_run=mark_uses,
                    chat_history=lambda: tuple(history),
                )
        for embed in workshop.embeds:
            _embed(embed)
        if workshop.guide:
            with ui.expansion("Guía", icon="menu_book").classes("w-full seccion"):
                ui.markdown(workshop.guide.read_text(encoding="utf-8"))
