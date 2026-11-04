# producto
# Este archivo es parte del producto: el asistente de onboarding que se
# entrega y se evalúa.

"""Lo que comparten todas las pantallas de la interfaz: estilo, barra lateral y
sesión. La sesión (quién entró, el modelo, el modo oscuro) vive en el navegador
(ver prefs.py)."""

from collections.abc import Callable
from typing import NamedTuple

from nicegui import ui

from onboarding.llm import ModelCatalog
from onboarding.ui import prefs as browser_prefs

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


def setup_page():
    """Estilo de la página. Devuelve el modo oscuro, que maneja la barra lateral."""
    # Arranca siguiendo al navegador (None); cada página aplica lo que haya guardado
    dark = ui.dark_mode(None)
    ui.add_head_html(STYLE)
    ui.colors(primary="#ff4b4b")
    for element in (ui.input, ui.textarea, ui.select, ui.number):
        element.default_props("filled stack-label")
    ui.button.default_props("no-caps unelevated")
    return dark


async def load_session(dark) -> dict:
    """Las preferencias guardadas en el navegador, con el modo oscuro ya aplicado."""
    prefs = await browser_prefs.load()
    dark.value = prefs.get("dark", prefs.get("prefers_dark", False))
    return prefs


# Lo que dura una sesión: quién entró y cómo. El modo oscuro y el modelo elegido
# quedan para la próxima vez.
SESSION_KEYS = ("person", "name", "as_manager", "test_key")


async def logout(prefs: dict) -> None:
    for key in SESSION_KEYS:
        prefs.pop(key, None)
    await browser_prefs.save(prefs)
    ui.navigate.to("./")  # a la entrada (todas las páginas cuelgan de /ui/)


# En el selector del modelo estructurado: usar lo que diga la configuración
# (LLM_STRUCTURED_MODEL o, si está vacío, el principal)
CONFIGURED = -1


class ModelSelects(NamedTuple):
    main: ui.select
    structured: ui.select | None  # solo si se pidió (los talleres)


def sidebar(
    prefs: dict,
    catalog: ModelCatalog,
    dark,
    title: str,
    extra: Callable[[], None] | None = None,
    structured: bool = False,
) -> ModelSelects:
    """Barra lateral: quién entró, `extra` (p. ej. el selector de taller), modelo
    principal y, con `structured`, el del perfil estructurado (ADR 0014), avisos de
    configuración, modo oscuro y cerrar sesión. Devuelve los selectores."""
    models = catalog.options

    async def on_dark_change(event) -> None:
        dark.value = event.value
        prefs["dark"] = event.value
        await browser_prefs.save(prefs)

    async def on_model_change(event) -> None:
        option = models[event.value]
        prefs["model"] = f"{option.provider}:{option.model}"
        await browser_prefs.save(prefs)

    async def on_structured_change(event) -> None:
        index = event.value
        prefs["structured_model"] = None if index == CONFIGURED else keys[index]
        await browser_prefs.save(prefs)

    # El modelo se guarda por nombre y no por posición: la lista cambia con el tiempo
    keys = [f"{option.provider}:{option.model}" for option in models]
    model_index = keys.index(prefs["model"]) if prefs.get("model") in keys else 0
    saved = prefs.get("structured_model")
    structured_index = keys.index(saved) if saved in keys else CONFIGURED
    structured_select = None

    with ui.left_drawer(value=True).props("width=336").classes("sidebar q-pa-lg"):
        ui.label(title).classes("text-subtitle1")
        if extra:
            extra()
        model_select = ui.select(
            {index: option.label for index, option in enumerate(models)},
            label="Modelo",
            value=model_index,
            on_change=on_model_change,
            with_input=True,  # filtra mientras escribís
        ).classes("w-full")
        if structured:
            options = {CONFIGURED: "Según la configuración"}
            options |= {index: option.label for index, option in enumerate(models)}
            structured_select = ui.select(
                options,
                label="Modelo para datos estructurados",
                value=structured_index,
                on_change=on_structured_change,
                with_input=True,
            ).classes("w-full")
        if catalog.notes:
            # Problemas del .env o de los proveedores (modelos que faltan, Ollama
            # apagado...): a la vista, sin tener que leer los logs.
            with ui.expansion(f"Avisos ({len(catalog.notes)})", icon="warning").classes(
                "w-full seccion avisos"
            ):
                for note in catalog.notes:
                    ui.markdown(note).classes("text-caption")
        ui.switch("Modo oscuro", value=dark.value, on_change=on_dark_change)
        ui.button("Cerrar sesión", on_click=lambda: logout(prefs), color=None).props(
            "outline"
        ).classes("boton-borde q-mt-md")
    return ModelSelects(model_select, structured_select)


def page_frame(path: str, height: str = "70vh"):
    """Una página de la app adentro de otra (el panel del jefe, por ejemplo)."""
    return (
        ui.element("iframe")
        .props(f'src="{path}"')
        .classes("w-full")
        .style(f"height: {height}; border: 1px solid rgba(49, 51, 63, 0.2); border-radius: 0.5rem")
    )
