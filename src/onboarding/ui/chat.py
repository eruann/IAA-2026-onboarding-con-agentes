# producto
# Este archivo es parte del producto: el asistente de onboarding que se
# entrega y se evalúa.

"""El chat con los agentes: lo usan las pantallas de Empleado y Jefe y los
talleres. Si un mensaje falla, ofrece reintentarlo con otro modelo."""

from collections.abc import Callable

from nicegui import run, ui

from onboarding.agents import TurnError, path_text, run_turn
from onboarding.llm import ModelOption, get_chat_model
from onboarding.ui.errors import explain, render_error


def _bubble(who: str, name: str):
    """Un mensaje del chat: avatar, nombre y una tarjeta redondeada. Devuelve la
    tarjeta para llenarla (con texto, un spinner o un error)."""
    mine = who == "user"
    with ui.row().classes(f"w-full no-wrap items-start gap-3 {'justify-end' if mine else ''}"):
        if not mine:
            ui.avatar("smart_toy", color=None).classes("avatar-asistente")
        with ui.column().classes(f"gap-1 {'items-end' if mine else ''} max-w-[85%]"):
            ui.label(name).classes("text-caption texto-suave")
            card = ui.element("div").classes(
                f"burbuja {'burbuja-mia' if mine else 'burbuja-asistente'}"
            )
        if mine:
            ui.avatar("person", color=None).classes("avatar-mio")
    return card


def next_model(current: int, total: int) -> int | None:
    """El modelo que sigue en la lista (al final vuelve al primero); None si hay uno solo."""
    return (current + 1) % total if total > 1 else None


# recorrido: chat-taller
def chat(
    models: list[ModelOption],
    model_select,
    name: str,
    intent: str | None = None,
    on_turn: Callable[[list[str], str | None], None] | None = None,
    greeting: str | None = None,
) -> list[tuple[str, str]]:
    """Chat con el agente. `intent`: a qué nodo va (None: decide el coordinador).
    `on_turn(path, failed)` se llama después de cada mensaje, salga bien o falle
    (los talleres marcan el recorrido en el grafo). Devuelve la conversación (se va
    llenando), para las pruebas que la usan.

    Si un mensaje falla, su globo ofrece reintentarlo con otro modelo. Esos botones
    valen mientras el mensaje que falló sea lo último de la conversación.
    """
    history: list[tuple[str, str]] = []
    retry_buttons: list = []  # los del último mensaje que falló (como mucho, un par)
    ui.label(
        greeting
        or f"Hola {name}, preguntame quién es quién en la empresa o cómo funciona Tesorería."
    ).classes("texto-suave")
    messages = ui.column().classes("w-full gap-4 q-my-sm")

    def disable_retry() -> None:
        for button in retry_buttons:
            button.disable()
        retry_buttons.clear()

    def offer_retry(text: str, bubble, footer, failed_index: int) -> None:
        async def retry(index: int) -> None:
            disable_retry()
            # El reintento borra estos botones: sin un contexto propio, lo que viene
            # después (avisarle al grafo) quedaría colgado del botón borrado.
            with messages:
                await answer(text, bubble, footer, index, retrying=True)

        async def auto() -> None:
            following = next_model(failed_index, len(models))
            if following is None:
                ui.notify("No hay otro modelo en la lista.", type="warning")
                return
            model_select.value = following  # cambia el selector y queda guardado
            await retry(following)

        async def manual() -> None:
            if model_select.value == failed_index:
                ui.notify(
                    "Elegí otro modelo en la barra lateral y volvé a tocar este botón.",
                    type="warning",
                )
                return
            await retry(model_select.value)

        with ui.row().classes("gap-2"):
            for label, icon, action in (
                ("Usar otro modelo (Auto)", "autorenew", auto),
                ("Usar otro modelo (manual)", "tune", manual),
            ):
                retry_buttons.append(
                    ui.button(label, icon=icon, on_click=action, color=None)
                    .props("outline size=sm")
                    .classes("boton-borde")
                )

    async def answer(text: str, bubble, footer, index: int, retrying: bool = False) -> None:
        option = models[index]
        bubble.clear()
        footer.clear()
        with bubble, ui.row().classes("items-center gap-2"):
            ui.spinner("dots", size="md")
            if retrying:
                ui.label(f"Probando con {option.label}…").classes("texto-suave")
        try:
            result = await run.io_bound(
                lambda: run_turn(
                    text,
                    intent=intent,
                    actor_name=name,
                    history=list(history),
                    model=get_chat_model(provider=option.provider, model=option.model),
                )
            )
        except Exception as failure:  # la pregunta falló: no queda en el historial
            error = failure.__cause__ if isinstance(failure, TurnError) else failure
            path, failed = (
                (failure.path, failure.failed_node)
                if isinstance(failure, TurnError)
                else ([], None)
            )
            bubble.clear()
            with bubble:
                render_error(error)
            with footer:
                if failed:
                    ui.label(path_text(path, failed)).classes("text-caption texto-suave")
                # Si lo que falta es un TODO, cambiar de modelo no lo arregla
                if explain(error)[0] != "pending":
                    offer_retry(text, bubble, footer, index)
            if on_turn:
                on_turn(path, failed)
            return
        bubble.clear()
        with bubble:
            ui.markdown(result.output)
        with footer:
            ui.label(path_text(result.path)).classes("text-caption texto-suave")
        history.extend([("user", text), ("assistant", result.output)])
        if on_turn:
            on_turn(result.path, None)

    async def send() -> None:
        text = box.value.strip()
        if not text:
            return
        box.value = ""
        disable_retry()  # una pregunta nueva deja atrás a la que falló
        with messages:
            with _bubble("user", name):
                ui.markdown(text)
            bubble = _bubble("assistant", "Onboarding")
        with bubble.parent_slot.parent:
            footer = ui.column().classes("gap-2")
        await answer(text, bubble, footer, model_select.value)

    with ui.row().classes("w-full items-center no-wrap"):
        box = (
            ui.input(placeholder="Escribí tu pregunta acá...")
            .classes("flex-grow")
            .on("keydown.enter", send)
        )
        ui.button(icon="send", on_click=send).props("flat round")
    return history
