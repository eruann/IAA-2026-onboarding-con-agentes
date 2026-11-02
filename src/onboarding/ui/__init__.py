# andamiaje
# Este archivo es andamiaje: una ayuda para que el equipo de estudiantes
# construya, pruebe o entienda el producto (talleres, diagramas, guías).
# No es parte del producto.

"""Interfaz web (NiceGUI), montada en la misma app FastAPI bajo /ui.

Un solo proceso y un solo servicio en Render: la API, el panel, Slack y esta
interfaz. Titular: Tech Lead.
"""

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

    from onboarding.ui import pages  # noqa: F401  (registra las páginas)

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
