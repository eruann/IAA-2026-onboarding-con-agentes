# producto
# Este archivo es parte del producto: el asistente de onboarding que se
# entrega y se evalúa.

"""La entrada (`/ui/`): elegís con qué persona de la empresa entrás.

Sin tildar nada vas a la pantalla del Empleado; con "Entrar como jefe", a la del
Jefe. Aparte, el botón de los talleres (Test) para el equipo: ver access.py.
"""

from nicegui import run, ui

from onboarding.config import get_settings
from onboarding.game import list_people
from onboarding.ui import prefs as browser_prefs
from onboarding.ui.access import check_password, workshops_key, workshops_mode
from onboarding.ui.layout import load_session, setup_page


def _test_button(prefs: dict) -> None:
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

    def entrar() -> None:
        if not check_password(settings, password.value):
            ui.notify("Clave incorrecta.", type="negative")
            return
        prefs["test_key"] = workshops_key(password.value)
        browser_prefs.save(prefs)
        ui.navigate.to("talleres")

    with ui.dialog() as dialog, ui.card().classes("w-80"):
        ui.label("Talleres del equipo").classes("text-h6")
        password = (
            ui.input("Clave", password=True, password_toggle_button=True)
            .classes("w-full")
            .on("keydown.enter", entrar)
        )
        ui.button("Entrar", on_click=entrar).classes("w-full")
    ui.button("Talleres (Test)", icon="lock", color=None, on_click=dialog.open).props(
        "outline"
    ).classes("boton-borde w-full")


# recorrido: entrada
@ui.page("/", response_timeout=20)
async def entry() -> None:
    dark = setup_page()
    prefs = await load_session(dark)
    try:
        people = await run.io_bound(list_people)
    except Exception:  # sin base no hay a quién elegir: se avisa y se puede ir a Test
        people = []

    with ui.card().classes("absolute-center w-96 q-pa-lg gap-4"):
        ui.label("Onboarding").classes("text-h5")
        if not people:
            ui.label(
                "Todavía no hay personas cargadas. Cargá la empresa ficticia con "
                "`docker compose run --rm app python -m onboarding.seed`."
            ).classes("texto-suave")
        else:
            by_key = {person.key: person for person in people}
            options = {
                person.key: f"{person.name} · {person.role}"
                + (" (ingresante)" if person.is_newcomer else "")
                for person in people
            }
            person_select = ui.select(
                options,
                label="¿Quién sos?",
                value=prefs.get("person") if prefs.get("person") in by_key else None,
                with_input=True,  # filtra mientras escribís
            ).classes("w-full")
            # Provisorio: hasta que se sepa quién es jefe de quién (ver game/people.py)
            as_manager = ui.checkbox("Entrar como jefe", value=bool(prefs.get("as_manager")))

            def entrar() -> None:
                person = by_key.get(person_select.value)
                if person is None:
                    ui.notify("Elegí una persona.", type="warning")
                    return
                prefs.update(person=person.key, name=person.name, as_manager=as_manager.value)
                browser_prefs.save(prefs)
                ui.navigate.to("jefe" if as_manager.value else "empleado")

            ui.button("Entrar", on_click=entrar).classes("w-full")
        _test_button(prefs)
