# producto
# Este archivo es parte del producto: el asistente de onboarding que se
# entrega y se evalúa.

"""Preferencias de quien usa la interfaz, guardadas en su navegador (localStorage).

Nombre, modelo elegido y modo oscuro. Viven en el navegador y no en el servidor:
sobreviven a reinicios del contenedor y a los deploys, y cada navegador tiene las
suyas.
"""

import json

from nicegui import ui

KEY = "onboarding"


async def load() -> dict:
    """Las preferencias guardadas, más `prefers_dark`: si el navegador prefiere oscuro."""
    prefs = await ui.run_javascript(
        f"""(() => {{
            const prefs = JSON.parse(localStorage.getItem("{KEY}") || "{{}}");
            prefs.prefers_dark = window.matchMedia("(prefers-color-scheme: dark)").matches;
            return prefs;
        }})()""",
        timeout=5,
    )
    return prefs or {}


def save(prefs: dict) -> None:
    stored = {key: value for key, value in prefs.items() if key != "prefers_dark"}
    ui.run_javascript(f"localStorage.setItem({json.dumps(KEY)}, {json.dumps(json.dumps(stored))})")
