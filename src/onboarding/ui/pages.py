# andamiaje
# Este archivo es andamiaje: una ayuda para que el equipo de estudiantes
# construya, pruebe o entienda el producto (talleres, diagramas, guías).
# No es parte del producto.

"""Páginas de la interfaz: entrada con nombre y talleres.

Retoma el primer prototipo de interfaz del proyecto (PR #15): entrada con
nombre, barra lateral con selector de modelo y cerrar sesión, chat con el agente
de onboarding y prueba de extracción de relaciones. Acá cada rol tiene su taller.
"""

import json
from pathlib import Path

from nicegui import run, ui

from onboarding.agents import load_lineage, run_turn
from onboarding.llm import ModelCatalog, ModelOption, get_chat_model, model_catalog
from onboarding.ui import prefs as browser_prefs
from onboarding.ui.tool_form import render_error, tool_card
from onboarding.workshop import UPCOMING, Embed, Workshop, all_workshops


def _login(prefs: dict) -> None:
    def comenzar() -> None:
        if name.value.strip():
            prefs["name"] = name.value.strip()
            browser_prefs.save(prefs)
            ui.navigate.reload()

    with ui.card().classes("absolute-center w-80"):
        ui.label("Onboarding").classes("text-h5")
        name = ui.input("¿Cómo te llamás?").classes("w-full").on("keydown.enter", comenzar)
        ui.button("Comenzar", on_click=comenzar).classes("w-full")


def _logout(prefs: dict) -> None:
    # Solo el nombre: el modo oscuro y el modelo elegido quedan para la próxima vez
    prefs.pop("name", None)
    browser_prefs.save(prefs)
    ui.navigate.reload()


def _bubble(who: str, name: str):
    """Un mensaje del chat: avatar, nombre y una tarjeta redondeada. Devuelve la
    tarjeta para llenarla (con texto, un spinner o un error)."""
    mine = who == "user"
    with ui.row().classes(f"w-full no-wrap items-start gap-3 {'justify-end' if mine else ''}"):
        if not mine:
            ui.avatar("smart_toy", color=None).classes("avatar-asistente")
        with ui.column().classes(f"gap-1 {'items-end' if mine else ''} max-w-[85%]"):
            ui.label(name).classes("text-caption texto-suave")
            card = ui.element("div").classes(
                f"burbuja {'burbuja-mia' if mine else 'burbuja-asistente'}"
            )
        if mine:
            ui.avatar("person", color=None).classes("avatar-mio")
    return card


# recorrido: chat-taller
def _chat(workshop: Workshop, models: list[ModelOption], model_select, name: str, on_turn) -> None:
    """Chat con el agente del taller. `on_turn(path)` se llama después de cada respuesta."""
    history: list[tuple[str, str]] = []
    ui.label(
        f"Hola {name}, preguntame quién es quién en la empresa o cómo funciona Tesorería."
    ).classes("texto-suave")
    messages = ui.column().classes("w-full gap-4 q-my-sm")

    async def enviar() -> None:
        text = box.value.strip()
        if not text:
            return
        box.value = ""
        option = models[model_select.value]
        with messages:
            with _bubble("user", name):
                ui.markdown(text)
            answer = _bubble("assistant", "Onboarding")
        with answer:
            ui.spinner("dots", size="md")
        try:
            result = await run.io_bound(
                lambda: run_turn(
                    text,
                    intent=workshop.intent,
                    actor_name=name,
                    history=list(history),
                    model=get_chat_model(provider=option.provider, model=option.model),
                )
            )
        except Exception as error:  # la pregunta falló: no queda en el historial
            answer.clear()
            with answer:
                render_error(error)
            return
        answer.clear()
        with answer:
            ui.markdown(result.output)
        with answer.parent_slot.parent:
            ui.label("Recorrido: Inicio → " + " → ".join(result.path) + " → Fin").classes(
                "text-caption texto-suave"
            )
        history.extend([("user", text), ("assistant", result.output)])
        on_turn(result.path)

    with ui.row().classes("w-full items-center no-wrap"):
        box = (
            ui.input(placeholder="Escribí tu pregunta acá...")
            .classes("flex-grow")
            .on("keydown.enter", enviar)
        )
        ui.button(icon="send", on_click=enviar).props("flat round")


# Aspecto parecido a Streamlit (el primer prototipo de interfaz era Streamlit)
STYLE = """
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Source+Sans+3:wght@400;600;700&family=Kalam&display=swap"
      rel="stylesheet">
<style>
  body, .q-field, .q-btn, .q-item, .q-chat-message { font-family: "Source Sans 3", sans-serif; }
  body { background-color: #ffffff; color: #31333f; font-size: 16px; }
  .sidebar { background-color: #f0f2f6 !important; }
  .titulo { font-size: 2.75rem; font-weight: 700; line-height: 1.2; }
  /* Expanders: borde fino gris, ícono a la izquierda y flecha a la derecha */
  .seccion { border: 1px solid rgba(49, 51, 63, 0.2); border-radius: 0.5rem; }
  .seccion .q-expansion-item__container > .q-item { font-size: 1rem; min-height: 2.75rem; }
  /* Campos rellenos en gris, sin la línea de abajo de Material */
  .q-field--filled .q-field__control { background: #f0f2f6; border-radius: 0.5rem; }
  .q-field--filled .q-field__control:before,
  .q-field--filled .q-field__control:after { display: none; }
  .q-field--filled.q-field--focused .q-field__control { box-shadow: inset 0 0 0 1px #ff4b4b; }
  .sidebar .q-field--filled .q-field__control { background: #ffffff; }
  /* Botones como los de Streamlit: blancos con borde gris */
  .q-btn { border-radius: 0.5rem; }
  .q-btn--outline:before { border-color: rgba(49, 51, 63, 0.2); }
  /* Modo oscuro, con los colores del modo oscuro de Streamlit */
  body.body--dark { background-color: #0e1117; color: #fafafa; }
  .body--dark .sidebar { background-color: #262730 !important; }
  .body--dark .seccion { border-color: rgba(250, 250, 250, 0.2); }
  .body--dark .q-field--filled .q-field__control { background: #262730; }
  .body--dark .sidebar .q-field--filled .q-field__control { background: #0e1117; }
  .body--dark .q-btn--outline:before { border-color: rgba(250, 250, 250, 0.2); }
  /* Clases propias y no las de Quasar (text-grey-*): Quasar va en una capa CSS
     con !important y no se puede pisar desde acá para el modo oscuro. */
  .texto-suave { color: #5c5f6b; }
  /* El grafo va sobre una "pizarra" blanca también en modo oscuro */
  .pizarra { background: #ffffff; border-radius: 0.75rem; padding: 0.5rem; }
  /* Recorrido del último mensaje: solo el borde de cada caja (el último trazo
     que dibuja rough.js; el primero es el relleno) y las líneas */
  .pizarra [data-id].resaltado:not(.flecha) > g > path:last-of-type,
  .pizarra .flecha.resaltado path { stroke: #e11d48; stroke-width: 3; transition: stroke 0.2s; }
  .avisos .q-expansion-item__container > .q-item { color: #b26b00; }
  .body--dark .avisos .q-expansion-item__container > .q-item { color: #ffbd45; }
  /* Globos del chat */
  .burbuja { padding: 0.75rem 1rem; border-radius: 1rem; line-height: 1.5; }
  .burbuja .nicegui-markdown > :first-child { margin-top: 0; }
  .burbuja .nicegui-markdown > :last-child { margin-bottom: 0; }
  .burbuja-mia { background: #f0f2f6; border-top-right-radius: 0.25rem; }
  .burbuja-asistente { background: #e6f4ea; border-top-left-radius: 0.25rem; }
  .avatar-mio { background: #ff4b4b; color: #ffffff; font-size: 2rem; }
  .avatar-asistente { background: #ffbd45; color: #31333f; font-size: 2rem; }
  .body--dark .burbuja-mia { background: #262730; }
  .body--dark .burbuja-asistente { background: #1c3326; }
  .boton-borde { color: #31333f; }
  .body--dark .texto-suave { color: #b0b4c1; }
  .body--dark .boton-borde { color: #fafafa; }
</style>
"""


def _style():
    """Estilo de la página. Devuelve el modo oscuro, que maneja la barra lateral."""
    # Arranca siguiendo al navegador (None); index() aplica lo que haya guardado
    dark = ui.dark_mode(None)
    ui.add_head_html(STYLE)
    ui.add_head_html(f'<script type="module">{GRAPH_JS}</script>')
    ui.colors(primary="#ff4b4b")
    for element in (ui.input, ui.textarea, ui.select, ui.number):
        element.default_props("filled stack-label")
    ui.button.default_props("no-caps unelevated")
    return dark


def _sidebar(prefs: dict, workshops: list[Workshop], current: int, catalog: ModelCatalog, dark):
    """Barra lateral: sesión, taller, modelo, avisos de configuración, modo oscuro y
    cerrar sesión. Devuelve el selector de modelo."""
    models = catalog.options
    options = {index: item.role for index, item in enumerate(workshops)}
    options |= {f"proximo-{role}": f"{role} · próximamente" for role in UPCOMING}

    def cambiar_modo(event) -> None:
        dark.value = event.value
        prefs["dark"] = event.value
        browser_prefs.save(prefs)

    def cambiar_modelo(event) -> None:
        option = models[event.value]
        prefs["model"] = f"{option.provider}:{option.model}"
        browser_prefs.save(prefs)

    # El modelo se guarda por nombre y no por posición: la lista cambia con el tiempo
    keys = [f"{option.provider}:{option.model}" for option in models]
    model_index = keys.index(prefs["model"]) if prefs.get("model") in keys else 0

    def cambiar_taller(event) -> None:
        if isinstance(event.value, int):
            ui.navigate.to(f"?taller={event.value}")
        else:
            ui.notify("Ese taller todavía no existe: se suma en los próximos PRs.")
            event.sender.value = current

    with ui.left_drawer(value=True).props("width=336").classes("sidebar q-pa-lg"):
        ui.label(f"Sesión de {prefs['name']}").classes("text-subtitle1")
        ui.select(options, label="Taller", value=current, on_change=cambiar_taller).classes(
            "w-full"
        )
        model_select = ui.select(
            {index: option.label for index, option in enumerate(models)},
            label="Modelo",
            value=model_index,
            on_change=cambiar_modelo,
        ).classes("w-full")
        if catalog.notes:
            # Problemas del .env o de los proveedores (modelos que faltan, Ollama
            # apagado...): a la vista, sin tener que leer los logs.
            with ui.expansion(f"Avisos ({len(catalog.notes)})", icon="warning").classes(
                "w-full seccion avisos"
            ):
                for note in catalog.notes:
                    ui.markdown(note).classes("text-caption")
        ui.switch("Modo oscuro", value=dark.value, on_change=cambiar_modo)
        ui.button("Cerrar sesión", on_click=lambda: _logout(prefs), color=None).props(
            "outline"
        ).classes("boton-borde q-mt-md")
    return model_select


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
    "**⚙ modelo**: llama al modelo · **Borde rojo**: recorrido del último mensaje. "
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
    botón para ampliarlo. Devuelve la función que marca el recorrido de un mensaje."""
    lineage = load_lineage()
    last_path: list[str] = []

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
            "marca por dónde pasó."
        ).classes("texto-suave text-caption")
        drawing = drawing_area()
        with ui.expansion("Chequeos de reglas", icon="rule").classes("w-full seccion"):
            _checks(lineage)
    with ui.page_sticky(position="top-right", x_offset=16, y_offset=16):
        ui.button("Grafo", icon="account_tree", on_click=panel.toggle).props("outline")

    def draw(target, path) -> None:
        ui.run_javascript(
            f"dibujarGrafo('c{target.id}', {json.dumps(lineage)}, {json.dumps(list(path))})"
        )

    def open_big() -> None:
        big.open()
        draw(big_drawing, last_path)

    def mark(path: list[str] | tuple[str, ...]) -> None:
        last_path[:] = path
        for target in (drawing, big_drawing):
            ui.run_javascript(f"marcarRecorrido('c{target.id}', {json.dumps(list(path))})")

    draw(drawing, ())
    return mark


def _embed(embed: Embed) -> None:
    """Una página de la app dentro del taller (p. ej. el panel del jefe), con botón
    para recargarla después de cambiar su código."""
    with ui.expansion(embed.title, icon="web").classes("w-full seccion"):
        if embed.help:
            ui.label(embed.help).classes("texto-suave")
        frame = (
            ui.element("iframe")
            .props(f'src="{embed.path}"')
            .classes("w-full")
            .style("height: 70vh; border: 1px solid rgba(49, 51, 63, 0.2); border-radius: 0.5rem")
        )
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
@ui.page("/", response_timeout=20)
async def index(taller: int = 0) -> None:
    dark = _style()
    # Las preferencias viven en el navegador: hay que esperar a que se conecte
    prefs = await browser_prefs.load()
    dark.value = prefs.get("dark", prefs.get("prefers_dark", False))
    name = prefs.get("name")
    if not name:
        _login(prefs)
        return

    workshops = all_workshops()
    current = min(max(taller, 0), len(workshops) - 1)
    workshop = workshops[current]
    # La lista de modelos sale de OpenRouter y de Ollama: se pide fuera del hilo
    # principal para no trabar la página.
    catalog = await run.io_bound(model_catalog)
    models = catalog.options
    model_select = _sidebar(prefs, workshops, current, catalog, dark)
    mark_path = _graph_panel()

    # Una sola pantalla: el chat abierto y el resto en secciones que se despliegan
    with ui.column().classes("w-full max-w-3xl mx-auto q-px-md q-py-xl gap-4"):
        ui.label(workshop.role).classes("titulo")
        ui.label(workshop.summary).classes("texto-suave")
        with ui.expansion("Chat", icon="chat", value=True).classes("w-full seccion"):
            _chat(
                workshop,
                models,
                model_select,
                name,
                on_turn=mark_path,
            )
        with ui.expansion("Pruebas", icon="science").classes("w-full seccion"):
            for tool in workshop.tools:
                tool_card(tool, models, model_select.value)
        for embed in workshop.embeds:
            _embed(embed)
        if workshop.guide:
            with ui.expansion("Guía", icon="menu_book").classes("w-full seccion"):
                ui.markdown(workshop.guide.read_text(encoding="utf-8"))
