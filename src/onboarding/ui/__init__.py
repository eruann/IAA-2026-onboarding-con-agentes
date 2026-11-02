"""Interfaz web (NiceGUI), montada en la misma app FastAPI bajo /ui.

Un solo proceso y un solo servicio en Render: la API, el panel, Slack y esta
interfaz. Titular: Tech Lead.
"""

import secrets

from fastapi import FastAPI
from nicegui import core, ui

from onboarding.config import get_settings

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

    settings = get_settings()
    # Firma la cookie de sesión. Sin UI_STORAGE_SECRET se inventa una al arrancar:
    # anda, pero las sesiones se pierden cada vez que se reinicia la app.
    secret = (
        settings.ui_storage_secret.get_secret_value()
        if settings.ui_storage_secret
        else secrets.token_urlsafe(32)
    )
    ui.run_with(
        app,
        mount_path=MOUNT_PATH,
        title="Onboarding",
        language="es",
        dark=False,
        storage_secret=secret,
        show_welcome_message=False,
    )
    _configured = True
