"""Talleres: dónde cada rol prueba sus cosas desde la interfaz.

Cada rol declara su taller en un `workshop.py` dentro de su carpeta: a qué agente
le habla y qué funciones propias quiere probar sueltas, salteando el agente. No
hace falta saber nada de la interfaz: el formulario de cada prueba se arma solo
mirando la firma de la función (`describe_params`).

    WORKSHOP = Workshop(
        key="grafo",
        role="Grafo cultural y datos",
        agent="extract_knowledge",
        summary="...",
        tools=(Tool(extract_triples, "Extraer relaciones", "Pegá una conversación"),),
    )

Para sumar una prueba: escribir la función (con tipos), sumarla a `tools` y
agregarle su test. Ver la sección "Talleres" de AGENTS.md.
"""

import inspect
import types
import typing
from collections.abc import Callable
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Literal

from langchain_core.language_models import BaseChatModel

# Cómo se dibuja cada parámetro en la interfaz
ParamKind = Literal["text", "int", "float", "bool", "choice", "model"]


@dataclass(frozen=True)
class Tool:
    fn: Callable
    title: str
    help: str = ""


@dataclass(frozen=True)
class Workshop:
    key: str
    role: str
    # Agente del registro con el que se chatea en este taller. None: el mensaje
    # va al coordinador sin agente elegido (taller del coordinador).
    agent: str | None
    summary: str  # qué construye este rol, en una o dos líneas
    tools: tuple[Tool, ...] = ()
    guide: Path | None = None  # LEEME.md que la interfaz muestra


@dataclass(frozen=True)
class Param:
    name: str
    kind: ParamKind
    default: Any = None
    required: bool = True
    choices: tuple[str, ...] = field(default_factory=tuple)


def _kind_of(annotation: Any) -> tuple[ParamKind, tuple[str, ...]]:
    origin = typing.get_origin(annotation)
    if origin in (typing.Union, types.UnionType):
        # `X | None`: se dibuja como X, sin obligar a completarlo
        args = [arg for arg in typing.get_args(annotation) if arg is not type(None)]
        if len(args) == 1:
            return _kind_of(args[0])
    if origin is Literal:
        return "choice", tuple(str(arg) for arg in typing.get_args(annotation))
    if annotation is bool:
        return "bool", ()
    if annotation is int:
        return "int", ()
    if annotation is float:
        return "float", ()
    if annotation is str:
        return "text", ()
    if isinstance(annotation, type) and issubclass(annotation, BaseChatModel):
        return "model", ()
    raise TypeError(f"La interfaz no sabe dibujar un parámetro de tipo {annotation!r}")


# recorrido: formulario-automatico
def describe_params(fn: Callable) -> list[Param]:
    """Los parámetros de `fn` como campos de formulario.

    TypeError si a un parámetro le falta el tipo o es uno que la interfaz no dibuja.
    """
    hints = typing.get_type_hints(fn)
    params = []
    for name, parameter in inspect.signature(fn).parameters.items():
        if name not in hints:
            raise TypeError(f"{fn.__name__}: al parámetro {name!r} le falta el tipo")
        kind, choices = _kind_of(hints[name])
        has_default = parameter.default is not inspect.Parameter.empty
        params.append(
            Param(
                name=name,
                kind=kind,
                default=parameter.default if has_default else None,
                required=not has_default,
                choices=choices,
            )
        )
    return params


def all_workshops() -> list[Workshop]:
    """Los talleres de todos los roles, en el orden en que se muestran."""
    # Import adentro: cada módulo importa este archivo para declarar su taller.
    from onboarding.agents import WORKSHOPS as agents_workshops
    from onboarding.game import WORKSHOP as game_workshop
    from onboarding.knowledge import WORKSHOPS as knowledge_workshops

    return [*knowledge_workshops, game_workshop, *agents_workshops]
