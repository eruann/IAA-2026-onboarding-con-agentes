# producto
# Este archivo es parte del producto: el asistente de onboarding que se
# entrega y se evalúa.

"""La entrada (`/ui/`): elegís con qué persona de la empresa entrás.

Sin tildar nada vas a la pantalla del Empleado; con "Entrar como jefe", a la del
Jefe. Debajo, lo que agregue el andamiaje en `ENTRY_EXTRAS` (el botón de los
talleres, ver ui/access.py).
"""

from collections.abc import Callable

from nicegui import run, ui

from onboarding.game import list_people
from onboarding.ui import prefs as browser_prefs
from onboarding.ui.layout import load_session, setup_page

# Botones que suma el andamiaje debajo de "Entrar" (el de los talleres lo agrega
# ui/pages.py al cargarse). Sin andamiaje la lista queda vacía.
ENTRY_EXTRAS: list[Callable[[dict], None]] = []


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

            async def enter() -> None:
                person = by_key.get(person_select.value)
                if person is None:
                    ui.notify("Elegí una persona.", type="warning")
                    return
                prefs.update(person=person.key, name=person.name, as_manager=as_manager.value)
                await browser_prefs.save(prefs)
                ui.navigate.to("jefe" if as_manager.value else "empleado")

            ui.button("Entrar", on_click=enter).classes("w-full")
        for extra in ENTRY_EXTRAS:
            extra(prefs)
