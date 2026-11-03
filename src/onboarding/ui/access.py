# andamiaje
# Este archivo es andamiaje: una ayuda para que el equipo de estudiantes
# construya, pruebe o entienda el producto (talleres, diagramas, guías).
# No es parte del producto.

"""Quién entra a los talleres (botón Test de la entrada).

- En dev (`ENV=dev`, lo de cada uno en su compu): se entra directo.
- En prod (la demo en Render): solo si está `ADMIN_PASSWORD`, y pidiéndola. Sin
  clave, los talleres quedan desactivados.

Al acertar la clave, el navegador guarda una huella de ella (no la clave): así no
hay que escribirla en cada visita y nadie entra copiando un valor sin conocerla.
"""

import hashlib
from typing import Literal

from nicegui import ui

from onboarding.config import Settings, get_settings
from onboarding.ui import prefs as browser_prefs

WorkshopsMode = Literal["open", "password", "off"]


def workshops_mode(settings: Settings) -> WorkshopsMode:
    if settings.env == "dev":
        return "open"
    return "password" if settings.admin_password else "off"


def workshops_key(password: str) -> str:
    """La huella que se guarda en el navegador al acertar la clave."""
    return hashlib.sha256(f"onboarding-talleres:{password}".encode()).hexdigest()


def check_password(settings: Settings, password: str) -> bool:
    secret = settings.admin_password
    return bool(secret) and password == secret.get_secret_value()


def has_test_access(settings: Settings, prefs: dict) -> bool:
    mode = workshops_mode(settings)
    if mode == "open":
        return True
    if mode == "off":
        return False
    return prefs.get("test_key") == workshops_key(settings.admin_password.get_secret_value())


def workshops_button(prefs: dict) -> None:
    """Botón a los talleres: directo en dev, con clave en prod, oculto si no hay clave."""
    settings = get_settings()
    mode = workshops_mode(settings)
    if mode == "off":
        return
    if mode == "open":
        ui.button(
            "Talleres (Test)",
            icon="science",
            color=None,
            on_click=lambda: ui.navigate.to("talleres"),
        ).props("outline").classes("boton-borde w-full")
        return

    async def enter() -> None:
        if not check_password(settings, password.value):
            ui.notify("Clave incorrecta.", type="negative")
            return
        prefs["test_key"] = workshops_key(password.value)
        await browser_prefs.save(prefs)
        ui.navigate.to("talleres")

    with ui.dialog() as dialog, ui.card().classes("w-80"):
        ui.label("Talleres del equipo").classes("text-h6")
        password = (
            ui.input("Clave", password=True, password_toggle_button=True)
            .classes("w-full")
            .on("keydown.enter", enter)
        )
        ui.button("Entrar", on_click=enter).classes("w-full")
    ui.button("Talleres (Test)", icon="lock", color=None, on_click=dialog.open).props(
        "outline"
    ).classes("boton-borde w-full")
