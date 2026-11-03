# andamiaje
# Este archivo es andamiaje: una ayuda para que el equipo de estudiantes
# construya, pruebe o entienda el producto (talleres, diagramas, guías).
# No es parte del producto.

"""Talleres: dónde cada rol prueba sus cosas desde la interfaz web.

Cada rol declara su taller en un `workshop.py` de su carpeta: a qué agente le
habla el chat y qué funciones propias se prueban sueltas, sin pasar por el agente.
No hace falta saber nada de la interfaz: el formulario de cada prueba se arma
solo con la firma de la función (`describe_params`).

    WORKSHOP = Workshop(
        role="Grafo cultural y datos",
        intent="answer_question",
        summary="...",
        tools=(Tool(extract_triples, "Extraer relaciones", "Pegá una conversación"),),
    )

Para sumar una prueba: escribir la función con tipos, sumarla a `tools` y
agregarle su test. Ver la sección "Talleres" de AGENTS.md.
"""

import ast
import inspect
import textwrap
import types
import typing
from collections.abc import Callable, Iterable, Sequence
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Literal

from langchain_core.language_models import BaseChatModel

# Cómo se dibuja cada parámetro en la interfaz. "history" no se dibuja: recibe la
# conversación del chat del taller.
ParamKind = Literal["text", "int", "float", "bool", "choice", "model", "history"]

# Tipo para un parámetro que recibe la conversación del chat del taller: una tupla
# de (quién, texto), con quién = "user" o "assistant".
ChatHistory = typing.NewType("ChatHistory", tuple)


@dataclass(frozen=True)
class Tool:
    fn: Callable
    title: str
    help: str = ""


@dataclass(frozen=True)
class Embed:
    """Una página de la app que el taller muestra adentro, p. ej. el panel del jefe."""

    title: str
    path: str  # ruta dentro de la app, p. ej. "/panel"
    help: str = ""


@dataclass(frozen=True)
class Workshop:
    role: str  # nombre del rol, como en docs/roles.md: es el nombre del taller
    # A qué nodo del grafo va el chat de este taller. None: decide el coordinador.
    intent: str | None
    summary: str  # qué construye el rol, en una o dos líneas
    tools: tuple[Tool, ...] = ()
    guide: Path | None = None  # LEEME.md que muestra la interfaz
    embeds: tuple[Embed, ...] = ()  # páginas del rol que se ven dentro del taller


@dataclass(frozen=True)
class Param:
    name: str
    kind: ParamKind
    default: Any = None
    required: bool = True
    # Los valores tal cual (pueden no ser texto, p. ej. Literal[1, 2]): la interfaz
    # los pasa a texto solo para mostrarlos.
    choices: tuple[Any, ...] = field(default_factory=tuple)


def _kind_of(annotation: Any) -> tuple[ParamKind, tuple[Any, ...]]:
    origin = typing.get_origin(annotation)
    if origin in (typing.Union, types.UnionType):
        # `X | None`: se dibuja como X, sin obligar a completarlo
        args = [arg for arg in typing.get_args(annotation) if arg is not type(None)]
        if len(args) == 1:
            return _kind_of(args[0])
    if annotation is ChatHistory:
        return "history", ()
    if origin is Literal:
        return "choice", typing.get_args(annotation)
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


def is_pending(fn: Callable) -> bool:
    """True si la función todavía es un TODO: su cuerpo hace `raise NotImplementedError`.

    Mira el código sin ejecutarlo: nada de llamar a la base ni al modelo.
    """
    try:
        source = textwrap.dedent(inspect.getsource(fn))
    except (OSError, TypeError):
        return False
    function = next(
        node
        for node in ast.walk(ast.parse(source))
        if isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef)
    )
    for statement in function.body:
        if isinstance(statement, ast.Raise) and statement.exc is not None:
            raised = statement.exc.func if isinstance(statement.exc, ast.Call) else statement.exc
            if isinstance(raised, ast.Name) and raised.id == "NotImplementedError":
                return True
    return False


def markdown_table(headers: Sequence[str], rows: Iterable[Sequence[Any]]) -> str:
    """Una tabla Markdown, para las pruebas que devuelven un informe.

    Un "|" dentro de una celda la partiría en dos: se escapa.
    """

    def row(cells: Sequence[Any]) -> str:
        return "| " + " | ".join(str(cell).replace("|", "\\|") for cell in cells) + " |"

    return "\n".join([row(headers), "|" + "---|" * len(headers), *(row(cells) for cells in rows)])


# El orden de los talleres en el selector: el de docs/roles.md
ROLE_ORDER = (
    "Agentes y orquestación",
    "RAG y evaluación",
    "Grafo cultural y datos",
    "Experiencia",
    "Diseñador de misiones",
)


def all_workshops() -> list[Workshop]:
    """Los talleres que ya existen, en el orden de ROLE_ORDER.

    Cada paquete exporta los talleres de sus roles como `WORKSHOPS`.
    """
    # Import adentro: cada módulo importa este archivo para declarar su taller.
    from onboarding.agents import WORKSHOPS as agents_workshops
    from onboarding.game import WORKSHOPS as game_workshops
    from onboarding.knowledge import WORKSHOPS as knowledge_workshops

    workshops = [*agents_workshops, *knowledge_workshops, *game_workshops]
    position = {role: index for index, role in enumerate(ROLE_ORDER)}
    return sorted(workshops, key=lambda workshop: position.get(workshop.role, len(position)))


# Roles que todavía no tienen taller: la interfaz los muestra como "próximamente"
UPCOMING: tuple[str, ...] = ()
