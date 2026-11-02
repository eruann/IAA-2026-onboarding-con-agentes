# producto
# Este archivo es parte del producto: el asistente de onboarding que se
# entrega y se evalúa.

"""Las pantallas de quien usa el asistente: Empleado (`/ui/empleado`) y Jefe
(`/ui/jefe`). Las dos tienen el chat con el coordinador, que hace lo que después
va a hacer Slack, y un tablero propio al lado.

Son una base para que cada rol construya encima: los tableros muestran lo que ya
existe y dejan marcado lo que falta.
"""

from nicegui import run, ui

from onboarding.llm import model_catalog
from onboarding.ui.chat import chat
from onboarding.ui.layout import load_session, setup_page, sidebar


async def _screen(title: str, manager: bool):
    """Lo común: estilo, sesión, barra lateral. Devuelve (prefs, modelos, selector) o
    None si no entró nadie (y lo manda a la entrada)."""
    dark = setup_page()
    prefs = await load_session(dark)
    if not prefs.get("person") or (manager and not prefs.get("as_manager")):
        ui.navigate.to("./")
        return None
    catalog = await run.io_bound(model_catalog)
    model_select = sidebar(prefs, catalog, dark, title=f"{title} · {prefs['name']}")
    return prefs, catalog.options, model_select


# recorrido: pantalla-jefe
@ui.page("/jefe", response_timeout=20)
async def manager_screen() -> None:
    screen = await _screen("Jefe", manager=True)
    if screen is None:
        return
    prefs, models, model_select = screen
    with ui.row().classes("w-full no-wrap items-start q-pa-md gap-6"):
        with ui.column().classes("w-1/2 gap-4"):
            ui.label("Chat").classes("text-h6")
            chat(
                models,
                model_select,
                prefs["name"],
                greeting=f"Hola {prefs['name']}, preguntame por tu equipo o por la empresa.",
            )
        with ui.column().classes("w-1/2 gap-2"):
            ui.label("Misiones de tus ingresantes").classes("text-h6")
            # TODO(experiencia): mostrar solo el equipo de este jefe y aprobar con un
            # clic. Hoy el panel muestra las misiones de todos los ingresantes.
            ui.element("iframe").props('src="/panel"').classes("w-full").style(
                "height: 80vh; border: 1px solid rgba(49, 51, 63, 0.2); border-radius: 0.5rem"
            )


# recorrido: pantalla-empleado
@ui.page("/empleado", response_timeout=20)
async def employee_screen() -> None:
    screen = await _screen("Empleado", manager=False)
    if screen is None:
        return
    prefs, models, model_select = screen
    with ui.row().classes("w-full no-wrap items-start q-pa-md gap-6"):
        with ui.column().classes("w-1/2 gap-4"):
            ui.label("Chat").classes("text-h6")
            chat(models, model_select, prefs["name"])
        with ui.column().classes("w-1/2 gap-2"):
            ui.label("Mis misiones").classes("text-h6")
            # Llega en el próximo PR: sus misiones con estado, puntos y nivel.
            ui.label("Tus misiones, tus puntos y tu nivel van a aparecer acá.").classes(
                "texto-suave"
            )
