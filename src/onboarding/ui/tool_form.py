# andamiaje
# Este archivo es andamiaje: una ayuda para que el equipo de estudiantes
# construya, pruebe o entienda el producto (talleres, diagramas, guías).
# No es parte del producto.

"""Formulario automático para una prueba de un taller.

Lee la firma de la función (`describe_params`) y arma un campo por parámetro.
Si la función recibe un modelo, suma el selector de modelo y la opción de
comparar dos modelos lado a lado. Quien escribe el taller no toca este archivo.
"""

import asyncio
import dataclasses
import inspect
import json
from collections.abc import Callable
from typing import Any

from nicegui import run, ui

from onboarding.llm import ModelOption, get_chat_model
from onboarding.paths import repo_relative
from onboarding.ui.errors import render_error
from onboarding.workshop import Param, Tool, describe_params, is_pending


def _source(fn: Callable) -> str:
    return f"{repo_relative(inspect.getsourcefile(fn) or '')}:{inspect.getsourcelines(fn)[1]}"


def _rows(value: list) -> list[dict]:
    return [dataclasses.asdict(item) if dataclasses.is_dataclass(item) else item for item in value]


def render_result(value: Any) -> None:
    """Muestra el resultado según su forma: texto, sí/no, tabla o JSON."""
    if value is None or value == []:
        ui.label("Sin resultados.").classes("texto-suave italic")
    elif isinstance(value, bool):
        ui.label("✅ Sí" if value else "❌ No")
    elif isinstance(value, str):
        ui.markdown(value)
    elif isinstance(value, list) and all(
        dataclasses.is_dataclass(item) or isinstance(item, dict) for item in value
    ):
        rows = _rows(value)
        columns = [{"name": key, "label": key, "field": key, "align": "left"} for key in rows[0]]
        ui.table(
            rows=[{**row, "_fila": index} for index, row in enumerate(rows)],
            columns=columns,
            row_key="_fila",
        ).classes("w-full").props("wrap-cells")
    elif isinstance(value, list):
        ui.markdown("\n".join(f"- {item}" for item in value))
    elif dataclasses.is_dataclass(value) or isinstance(value, dict):
        data = dataclasses.asdict(value) if dataclasses.is_dataclass(value) else value
        ui.code(json.dumps(data, ensure_ascii=False, indent=2, default=str), language="json")
    else:
        ui.label(str(value))


def _field(param: Param):
    if param.kind == "text":
        return ui.textarea(param.name, value=param.default or "").classes("w-full")
    if param.kind == "int":
        return ui.number(param.name, value=param.default, precision=0)
    if param.kind == "float":
        return ui.number(param.name, value=param.default)
    if param.kind == "bool":
        return ui.switch(param.name, value=bool(param.default))
    options = {choice: str(choice) for choice in param.choices}
    return ui.select(options, label=param.name, value=param.default).classes("w-full")


def _value(param: Param, field) -> Any:
    value = field.value
    if param.kind == "int" and value is not None:
        return int(value)
    if param.kind == "text" and value == "" and not param.required:
        return param.default
    return value


# recorrido: tarjeta-prueba
def tool_card(
    tool: Tool,
    models: list[ModelOption],
    model_index: int,
    on_run: Callable | None = None,
    chat_history: Callable[[], tuple] = tuple,
) -> None:
    """La tarjeta de una prueba. `on_run(fn)` se llama cada vez que se corre;
    `chat_history()` da la conversación del chat, para los parámetros `ChatHistory`."""
    params = describe_params(tool.fn)
    fields: dict[str, Any] = {}
    model_param = next((param.name for param in params if param.kind == "model"), None)
    options = {index: option.label for index, option in enumerate(models)}

    with ui.expansion(tool.title, icon="play_circle").classes("w-full seccion"):
        with ui.row().classes("items-center gap-2"):
            if is_pending(tool.fn):
                ui.badge("pendiente", color="orange")
            ui.label(_source(tool.fn)).classes("text-caption texto-suave font-mono")
        if tool.help:
            ui.label(tool.help).classes("texto-suave")

        for param in params:
            if param.kind not in ("model", "history"):
                fields[param.name] = _field(param)
        if model_param:
            first = ui.select(options, label="Modelo", value=model_index).classes("w-full")
            compare = ui.switch("Comparar con otro modelo")
            second = ui.select(options, label="Segundo modelo", value=0).classes("w-full")
            second.bind_visibility_from(compare, "value")

        results = ui.row().classes("w-full items-start no-wrap gap-4")

        async def run_tool() -> None:
            missing = [
                p.name
                for p in params
                if p.required and p.name in fields and fields[p.name].value in (None, "")
            ]
            if missing:
                ui.notify(f"Completá: {', '.join(missing)}", type="warning")
                return
            kwargs = {p.name: _value(p, fields[p.name]) for p in params if p.name in fields}
            kwargs |= {p.name: chat_history() for p in params if p.kind == "history"}
            if on_run:
                on_run(tool.fn)
            chosen = [None]
            if model_param:
                chosen = [first.value] + ([second.value] if compare.value else [])

            results.clear()
            columns = []
            with results:
                for index in chosen:
                    with ui.column().classes("flex-1 min-w-0") as column:
                        if index is not None:
                            ui.label(models[index].label).classes("text-weight-bold")
                        ui.spinner("dots", size="lg")
                    columns.append(column)

            async def run_one(column, index) -> None:
                try:
                    call_kwargs = dict(kwargs)
                    if index is not None:
                        option = models[index]
                        call_kwargs[model_param] = get_chat_model(
                            provider=option.provider, model=option.model
                        )
                    value = await run.io_bound(tool.fn, **call_kwargs)
                    error = None
                except Exception as exc:  # se muestra en pantalla, explicado
                    error = exc
                column.clear()
                with column:
                    if index is not None:
                        ui.label(models[index].label).classes("text-weight-bold")
                    if error:
                        render_error(error)
                    else:
                        render_result(value)

            await asyncio.gather(*(run_one(c, i) for c, i in zip(columns, chosen, strict=True)))

        ui.button("Probar", on_click=run_tool, color=None).props("outline").classes("boton-borde")
