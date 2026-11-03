# producto
# Este archivo es parte del producto: el asistente de onboarding que se
# entrega y se evalúa.

"""Las pantallas de quien usa el asistente: Empleado (`/ui/empleado`) y Jefe
(`/ui/jefe`). Las dos tienen el chat con el coordinador, que hace lo que después
va a hacer Slack, y un tablero propio al lado.

Son una base para que cada rol construya encima: los tableros muestran lo que ya
existe (el Empleado, sus misiones, puntos y nivel; el Jefe, el panel) y dejan
marcado lo que falta.
"""

from nicegui import run, ui

from onboarding.game import STATUS_LABELS, EmployeeBoard, employee_board
from onboarding.llm import model_catalog
from onboarding.ui.chat import chat
from onboarding.ui.layout import load_session, page_frame, setup_page, sidebar

# El color de cada estado (el nombre sale de game.STATUS_LABELS, el mismo del panel)
STATUS_COLORS = {"pending": "grey-7", "submitted": "orange-8", "approved": "positive"}


def _employee_board(board: EmployeeBoard) -> None:
    """Nivel, puntos y una tarjeta por misión."""
    with ui.row().classes("items-center gap-3"):
        ui.badge(board.level, color="primary").classes("text-subtitle2 q-pa-sm")
        ui.label(f"{board.earned} puntos ganados · {board.available} para canjear").classes(
            "texto-suave"
        )
    if not board.missions:
        ui.label("Todavía no tenés misiones asignadas.").classes("texto-suave")
    for mission in board.missions:
        label = STATUS_LABELS.get(mission.status, mission.status)
        if mission.status == "rejected":
            label += ": revisala y volvé a entregar"
        color = STATUS_COLORS.get(mission.status, "negative")
        with ui.card().classes("w-full seccion shadow-none"):
            with ui.row().classes("w-full items-center no-wrap"):
                ui.label(mission.title).classes("text-subtitle1 text-weight-medium")
                ui.space()
                ui.badge(f"{mission.points} pts", color="grey-5")
            ui.badge(label, color=color)
            ui.label(mission.description).classes("texto-suave")
            ui.label(f"Evidencia: {mission.evidence_required}").classes("text-caption")
    # TODO(experiencia): entregar la evidencia desde acá (Evidence), el canje con
    # los puntos disponibles y el dial de tono. Hoy el tablero solo muestra.


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
            page_frame("/panel", height="80vh")


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
            board = await run.io_bound(employee_board, prefs["person"])
            _employee_board(board)
