"""Páginas de la interfaz: entrada con nombre y talleres.

Retoma el primer prototipo de interfaz del proyecto (PR #15): entrada con
nombre, barra lateral con selector de modelo y cerrar sesión, chat con el agente
de onboarding y prueba de extracción de relaciones. Acá cada rol tiene su taller.
"""

from nicegui import app, run, ui

from onboarding.agents import run_turn
from onboarding.llm import ModelOption, available_models, get_chat_model
from onboarding.ui.tool_form import render_error, tool_card
from onboarding.workshop import UPCOMING, Workshop, all_workshops


def _login() -> None:
    def comenzar() -> None:
        if name.value.strip():
            app.storage.user["name"] = name.value.strip()
            ui.navigate.reload()

    with ui.card().classes("absolute-center w-80"):
        ui.label("Onboarding").classes("text-h5")
        name = ui.input("¿Cómo te llamás?").classes("w-full").on("keydown.enter", comenzar)
        ui.button("Comenzar", on_click=comenzar).classes("w-full")


def _logout() -> None:
    app.storage.user.clear()
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
def _chat(workshop: Workshop, models: list[ModelOption], model_select, name: str) -> None:
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
<link href="https://fonts.googleapis.com/css2?family=Source+Sans+3:wght@400;600;700&display=swap"
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
    # None sigue al sistema; el interruptor de la barra lateral lo fija
    dark = ui.dark_mode(app.storage.user.get("dark"))
    ui.add_head_html(STYLE)
    ui.colors(primary="#ff4b4b")
    for element in (ui.input, ui.textarea, ui.select, ui.number):
        element.default_props("filled stack-label")
    ui.button.default_props("no-caps unelevated")
    return dark


def _sidebar(name: str, workshops: list[Workshop], current: int, models: list[ModelOption], dark):
    """Barra lateral: sesión, taller, modelo y cerrar sesión. Devuelve el selector de modelo."""
    options = {index: item.role for index, item in enumerate(workshops)}
    options |= {f"proximo-{role}": f"{role} · próximamente" for role in UPCOMING}

    def cambiar_modo(event) -> None:
        dark.value = event.value
        app.storage.user["dark"] = event.value

    def cambiar_taller(event) -> None:
        if isinstance(event.value, int):
            ui.navigate.to(f"?taller={event.value}")
        else:
            ui.notify("Ese taller todavía no existe: se suma en los próximos PRs.")
            event.sender.value = current

    with ui.left_drawer(value=True).props("width=336").classes("sidebar q-pa-lg"):
        ui.label(f"Sesión de {name}").classes("text-subtitle1")
        ui.select(options, label="Taller", value=current, on_change=cambiar_taller).classes(
            "w-full"
        )
        model_select = ui.select(
            {index: option.label for index, option in enumerate(models)},
            label="Modelo",
            value=min(app.storage.user.get("model", 0), len(models) - 1),
            on_change=lambda event: app.storage.user.update(model=event.value),
        ).classes("w-full")
        ui.switch("Modo oscuro", value=app.storage.user.get("dark") is True, on_change=cambiar_modo)
        ui.button("Cerrar sesión", on_click=_logout, color=None).props("outline").classes(
            "boton-borde q-mt-md"
        )
    return model_select


# recorrido: pagina-talleres
@ui.page("/", response_timeout=20)
async def index(taller: int = 0) -> None:
    dark = _style()
    name = app.storage.user.get("name")
    if not name:
        _login()
        return

    workshops = all_workshops()
    current = min(max(taller, 0), len(workshops) - 1)
    workshop = workshops[current]
    # La lista de modelos sale de OpenRouter y de Ollama: se pide fuera del hilo
    # principal para no trabar la página.
    models = await run.io_bound(available_models)
    model_select = _sidebar(name, workshops, current, models, dark)

    # Una sola pantalla: el chat abierto y el resto en secciones que se despliegan
    with ui.column().classes("w-full max-w-3xl mx-auto q-px-md q-py-xl gap-4"):
        ui.label(workshop.role).classes("titulo")
        ui.label(workshop.summary).classes("texto-suave")
        with ui.expansion("Chat", icon="chat", value=True).classes("w-full seccion"):
            _chat(workshop, models, model_select, name)
        with ui.expansion("Pruebas", icon="science").classes("w-full seccion"):
            for tool in workshop.tools:
                tool_card(tool, models, model_select.value)
        if workshop.guide:
            with ui.expansion("Guía", icon="menu_book").classes("w-full seccion"):
                ui.markdown(workshop.guide.read_text(encoding="utf-8"))
