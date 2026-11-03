# producto
# Este archivo es parte del producto: el asistente de onboarding que se
# entrega y se evalúa.

"""Interfaz web (NiceGUI), montada en la misma app FastAPI bajo /ui: la entrada,
las pantallas de Empleado y Jefe, y los talleres del equipo.

Un solo proceso y un solo servicio en Render: la API, el panel, Slack y esta
interfaz. Titular: Tech Lead.
"""

import importlib
import importlib.util

from fastapi import FastAPI
from nicegui import core, ui

MOUNT_PATH = "/ui"
_configured = False


# recorrido: montaje-ui
def mount(app: FastAPI) -> None:
    global _configured
    if _configured:
        # NiceGUI tiene una sola app por proceso y no se puede reconfigurar una vez
        # que arrancó. En producción create_app() corre una vez; en los tests, muchas.
        app.mount(MOUNT_PATH, core.app)
        return

    # Registran las páginas: la entrada y las pantallas de Empleado y Jefe (producto)
    from onboarding.ui import entry, screens  # noqa: F401

    # Los talleres son andamiaje: se registran solo si están. Sin ellos, el producto
    # funciona igual y /ui/talleres no existe (ver ADR 0013).
    if importlib.util.find_spec("onboarding.ui.pages"):
        importlib.import_module("onboarding.ui.pages")

    # Sin storage_secret: las preferencias (nombre, modelo, modo) viven en el
    # navegador (ui/prefs.py), no en sesiones del servidor.
    ui.run_with(
        app,
        mount_path=MOUNT_PATH,
        title="Onboarding",
        language="es",
        dark=None,
        show_welcome_message=False,
    )
    _configured = True
