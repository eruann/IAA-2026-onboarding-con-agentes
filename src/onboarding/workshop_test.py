import ast
import importlib
from pathlib import Path
from typing import Literal

import pytest
from langchain_core.language_models import BaseChatModel

from onboarding.workshop import (
    SECTIONS,
    ChatHistory,
    all_workshops,
    describe_params,
    is_pending,
    markdown_table,
    tool_origin,
    workshop_modules,
)


def _ejemplo(
    texto: str,
    cantidad: int = 3,
    umbral: float = 0.5,
    exacto: bool = False,
    modo: Literal["rápido", "lento"] = "rápido",
    model: BaseChatModel | None = None,
) -> str:
    return texto


def _pendiente() -> None:
    """Docstring antes del raise: sigue contando como pendiente."""
    raise NotImplementedError("TODO(rol): algo")


def _con_raise_condicional(value: int) -> int:
    if value < 0:
        raise NotImplementedError("solo este caso")
    return value


def test_cada_tipo_se_dibuja_con_su_campo() -> None:
    params = describe_params(_ejemplo)

    assert [(p.name, p.kind) for p in params] == [
        ("texto", "text"),
        ("cantidad", "int"),
        ("umbral", "float"),
        ("exacto", "bool"),
        ("modo", "choice"),
        ("model", "model"),
    ]
    assert params[0].required
    assert not params[1].required and params[1].default == 3
    assert params[4].choices == ("rápido", "lento")


def test_las_opciones_de_un_literal_mantienen_su_tipo() -> None:
    def con_numeros(cantidad: Literal[1, 2, 3] = 2) -> int:
        return cantidad

    assert describe_params(con_numeros)[0].choices == (1, 2, 3)


def test_un_selector_sin_valor_por_defecto_arranca_en_la_primera_opcion() -> None:
    def sin_default(modo: Literal["rápido", "lento"]) -> str:
        return modo

    param = describe_params(sin_default)[0]

    assert param.default == "rápido"
    assert param.required


def test_un_parametro_sin_tipo_falla_con_mensaje_claro() -> None:
    def sin_tipo(texto) -> str:
        return texto

    with pytest.raises(TypeError, match="le falta el tipo"):
        describe_params(sin_tipo)


def test_detecta_funciones_pendientes() -> None:
    assert is_pending(_pendiente)
    assert not is_pending(_con_raise_condicional)
    assert not is_pending(_ejemplo)


@pytest.mark.parametrize("workshop", all_workshops(), ids=lambda workshop: workshop.role)
def test_cada_taller_se_puede_dibujar(workshop) -> None:
    for tool in workshop.tools:
        describe_params(tool.fn)
    assert workshop.guide is not None and workshop.guide.exists()


def test_arma_una_tabla_markdown_y_escapa_el_pipe() -> None:
    assert markdown_table(("x", "y"), [("a | b", 3)]) == "| x | y |\n|---|---|\n| a \\| b | 3 |"


def test_los_talleres_salen_en_el_orden_de_los_roles() -> None:
    from onboarding.workshop import ROLE_ORDER

    roles = [workshop.role for workshop in all_workshops()]
    assert roles == [role for role in ROLE_ORDER if role in roles]
    assert len(roles) == len(set(roles))


@pytest.mark.parametrize("workshop", all_workshops(), ids=lambda workshop: workshop.role)
def test_cada_pagina_embebida_existe_en_la_app(workshop) -> None:
    from starlette.routing import Match

    from onboarding.api.main import app

    for embed in workshop.embeds:
        scope = {"type": "http", "path": embed.path, "method": "GET", "root_path": ""}
        assert any(route.matches(scope)[0] == Match.FULL for route in app.router.routes), (
            f"{workshop.role}: {embed.path} no es una ruta de la app"
        )


def test_la_conversacion_del_chat_no_se_dibuja_como_campo() -> None:
    def con_historia(pregunta: str, history: ChatHistory = ()) -> str:
        return pregunta

    assert [(p.name, p.kind) for p in describe_params(con_historia)] == [
        ("pregunta", "text"),
        ("history", "history"),
    ]


def test_los_talleres_cuyo_agente_no_responde_preguntas_tienen_su_saludo() -> None:
    # El saludo general invita a preguntar por la empresa: solo sirve para el
    # coordinador y para el agente que responde preguntas
    for workshop in all_workshops():
        if workshop.intent not in (None, "answer_question"):
            assert workshop.greeting, workshop.role


def test_el_origen_de_una_prueba_sale_de_su_archivo() -> None:
    from onboarding.agents.answer_question.checks import chunk_document
    from onboarding.agents.extract_knowledge.node import extract_triples
    from onboarding.knowledge import retrieve

    assert tool_origin(chunk_document) == "adhoc"
    assert tool_origin(extract_triples) == "agent"
    assert tool_origin(retrieve) == "common"


@pytest.mark.parametrize("module_name", workshop_modules())
def test_cada_workshop_ordena_sus_imports_en_las_tres_secciones(module_name: str) -> None:
    module = importlib.import_module(module_name)
    source = Path(module.__file__).read_text(encoding="utf-8")
    lines = source.splitlines()
    starts = {}
    for origin, header in SECTIONS.items():
        found = [number for number, line in enumerate(lines, 1) if line.startswith(header)]
        assert len(found) == 1, f"{module_name}: tiene que tener una vez «{header} …»"
        starts[origin] = found[0]
    assert list(starts.values()) == sorted(starts.values()), f"{module_name}: van en orden 1, 2, 3"

    package = module_name.rsplit(".", 1)[0]
    allowed = {
        "adhoc": lambda m: m == f"{package}.checks",
        "agent": lambda m: m == f"{package}.node",
        "common": lambda m: m.startswith("onboarding.") and not m.startswith("onboarding.agents."),
    }
    imported = {}
    for node in ast.walk(ast.parse(source)):
        if not isinstance(node, ast.ImportFrom) or not (node.module or "").startswith("onboarding"):
            continue
        section = next((o for o, start in reversed(starts.items()) if node.lineno > start), None)
        assert section, f"{module_name}:{node.lineno}: {node.module} va dentro de una sección"
        assert allowed[section](node.module), (
            f"{module_name}:{node.lineno}: {node.module} no va en «{SECTIONS[section]}»"
        )
        imported |= {alias.asname or alias.name: section for alias in node.names}

    for tool in module.WORKSHOP.tools:
        origin = tool_origin(tool.fn)
        assert imported.get(tool.fn.__name__) == origin, (
            f"{module_name}: «{tool.title}» ({tool.fn.__name__}) se importa en «{SECTIONS[origin]}»"
        )


def test_el_producto_no_importa_talleres_ni_pruebas_ad_hoc() -> None:
    # Los talleres y sus pruebas son andamiaje: el producto funciona sin ellos
    package = Path(__file__).parent
    problems = []
    for path in sorted(package.rglob("*.py")):
        text = path.read_text(encoding="utf-8")
        if path.name.endswith("_test.py") or not text.startswith("# producto"):
            continue
        for node in ast.walk(ast.parse(text)):
            if isinstance(node, ast.ImportFrom) and (node.module or "").endswith(
                (".workshop", ".checks")
            ):
                problems.append(f"{path.relative_to(package)}:{node.lineno} importa {node.module}")
    assert not problems, "\n".join(problems)
